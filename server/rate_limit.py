"""Atomic sliding-window quotas and leased concurrency over Upstash Redis REST."""
from dataclasses import dataclass
import asyncio
import hashlib
import ipaddress
import math
import os
import re
from urllib.parse import urlsplit
import uuid

import httpx


ACQUIRE_SCRIPT = """
local clock = redis.call('TIME')
local now = tonumber(clock[1]) * 1000 + math.floor(tonumber(clock[2]) / 1000)
local window = tonumber(ARGV[1])
local lease = tonumber(ARGV[5])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now - window)
redis.call('ZREMRANGEBYSCORE', KEYS[3], '-inf', now)
local retry = 0
for i = 1, 2 do
  if redis.call('ZCARD', KEYS[i]) >= tonumber(ARGV[i + 1]) then
    local first = redis.call('ZRANGE', KEYS[i], 0, 0, 'WITHSCORES')
    retry = math.max(retry, tonumber(first[2]) + window - now)
  end
end
if redis.call('ZCARD', KEYS[3]) >= tonumber(ARGV[4]) then
  local first = redis.call('ZRANGE', KEYS[3], 0, 0, 'WITHSCORES')
  retry = math.max(retry, tonumber(first[2]) - now)
end
if retry > 0 then return {0, retry} end
redis.call('ZADD', KEYS[1], now, ARGV[6])
redis.call('ZADD', KEYS[2], now, ARGV[6])
redis.call('ZADD', KEYS[3], now + lease, ARGV[6])
redis.call('PEXPIRE', KEYS[1], window)
redis.call('PEXPIRE', KEYS[2], window)
redis.call('PEXPIRE', KEYS[3], lease)
return {1, 0}
"""


class LimitUnavailable(Exception):
    pass


class LimitExceeded(Exception):
    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__('Shared chat quota exhausted')


def client_identity(headers, socket_ip):
    # Vercel overwrites this header at its public ingress. No direct/local
    # deployment may opt into that trust merely by supplying the header.
    raw = headers.get('x-forwarded-for', '').split(',')[0].strip() if os.getenv('VERCEL') == '1' else socket_ip
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError as error:
        raise LimitUnavailable('Invalid ingress identity') from error


@dataclass(frozen=True)
class Settings:
    url: str
    token: str
    namespace: str = 'portfolio-chat'
    per_ip: int = 10
    global_limit: int = 60
    concurrency: int = 8
    window_ms: int = 60_000
    lease_ms: int = 32_000

    @classmethod
    def from_environment(cls):
        url = os.getenv('UPSTASH_REDIS_REST_URL', '').rstrip('/')
        token = os.getenv('UPSTASH_REDIS_REST_TOKEN', '')
        try:
            parts = urlsplit(url)
            _ = parts.port
        except ValueError as error:
            raise LimitUnavailable('Invalid shared limiter endpoint') from error
        namespace = os.getenv('CHAT_RATE_NAMESPACE', 'portfolio-chat')
        if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
                or parts.path or parts.query or parts.fragment or not token
                or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', namespace)):
            raise LimitUnavailable('Shared limiter is not configured')
        try:
            global_limit = int(os.getenv('CHAT_GLOBAL_RATE_LIMIT', '60'))
            concurrency = int(os.getenv('CHAT_MAX_CONCURRENT', '8'))
            if not 1 <= global_limit <= 10_000 or not 1 <= concurrency <= 100:
                raise ValueError()
        except ValueError as error:
            raise LimitUnavailable('Invalid shared limiter limits') from error
        return cls(url=url, token=token, namespace=namespace,
                   global_limit=global_limit, concurrency=concurrency)


def uses_shared_store():
    # Production never silently falls back to independent process quotas.
    return os.getenv('VERCEL') == '1' or bool(os.getenv('UPSTASH_REDIS_REST_URL') or os.getenv('UPSTASH_REDIS_REST_TOKEN'))


class SharedLimiter:
    def __init__(self, settings, http=None):
        self.settings = settings
        self.http = http
        # Hash tags keep all three keys in the same Redis cluster slot.
        self.prefix = '{' + settings.namespace + '}:'
        self.leases_key = self.prefix + 'leases'

    def command(self, values, timeout=2):
        try:
            # No retry: a lost response could already have reserved quota.
            sender = self.http.post if self.http else httpx.post
            response = sender(self.settings.url, json=values,
                              headers={'Authorization': 'Bearer ' + self.settings.token},
                              timeout=timeout, follow_redirects=False)
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict) or 'error' in result or 'result' not in result:
                raise ValueError('Invalid limiter response')
            return result['result']
        except (httpx.HTTPError, ValueError, TypeError) as error:
            raise LimitUnavailable('Shared limiter unavailable') from error

    def acquisition(self, identity):
        digest = hashlib.sha256(identity.encode()).hexdigest()
        lease_id = uuid.uuid4().hex
        s = self.settings
        return lease_id, ['EVAL', ACQUIRE_SCRIPT, 3, self.prefix + 'ip:' + digest,
                               self.prefix + 'global', self.leases_key,
                               s.window_ms, s.per_ip, s.global_limit, s.concurrency, s.lease_ms, lease_id]

    def verdict(self, result, lease_id):
        if (not isinstance(result, list) or len(result) != 2
                or any(type(item) is not int for item in result)
                or result[0] not in (0, 1) or result[1] < 0):
            raise LimitUnavailable('Invalid limiter verdict')
        if result[0] == 0:
            raise LimitExceeded(max(1, math.ceil(result[1] / 1000)))
        return lease_id

    def acquire(self, identity, timeout=2):
        lease_id, command = self.acquisition(identity)
        return self.verdict(self.command(command, timeout), lease_id)

    def release(self, lease_id, timeout=2):
        result = self.command(['ZREM', self.leases_key, lease_id], timeout)
        if type(result) is not int or result not in (0, 1):
            raise LimitUnavailable('Invalid lease release')


class AsyncSharedLimiter(SharedLimiter):
    async def command(self, values, timeout=2):
        try:
            async with asyncio.timeout(timeout):
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                    response = await client.post(self.settings.url, json=values,
                        headers={'Authorization': 'Bearer ' + self.settings.token})
                    response.raise_for_status()
                    result = response.json()
                    if not isinstance(result, dict) or 'error' in result or 'result' not in result:
                        raise ValueError('Invalid limiter response')
                    return result['result']
        except (httpx.HTTPError, ValueError, TypeError, TimeoutError) as error:
            raise LimitUnavailable('Shared limiter unavailable') from error

    async def acquire(self, identity, timeout=2):
        lease_id, command = self.acquisition(identity)
        return self.verdict(await self.command(command, timeout), lease_id)

    async def release(self, lease_id, timeout=2):
        result = await self.command(['ZREM', self.leases_key, lease_id], timeout)
        if type(result) is not int or result not in (0, 1):
            raise LimitUnavailable('Invalid lease release')
