"""Opt-in hosted Redis check using a unique, expiring test namespace."""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.rate_limit import Settings, AsyncSharedLimiter, LimitExceeded, ACQUIRE_SCRIPT


async def check(report):
    settings = replace(Settings.from_environment(), namespace='portfolio-check-' + uuid.uuid4().hex[:12], per_ip=2)
    times = []
    class Probe(AsyncSharedLimiter):
        async def command(self, values, timeout=2):
            started = time.monotonic()
            try:
                return await super().command(values, timeout)
            finally:
                times.append(time.monotonic() - started)
    workers = [Probe(settings) for _ in range(3)]
    identity = '192.0.2.1'  # documentation-only address, never a visitor IP
    async def acquire(worker):
        try:
            return await worker.acquire(identity)
        except LimitExceeded:
            return None
    leases = await asyncio.gather(*(acquire(worker) for worker in workers))
    active = [lease for lease in leases if lease]
    try:
        if len(active) != 2:
            raise ValueError('Atomic quota mismatch')
        if await acquire(Probe(settings)) is not None:
            raise ValueError('Fresh client lost quota state')
        ip_key = workers[0].prefix + 'ip:' + hashlib.sha256(identity.encode()).hexdigest()
        ttl = await workers[0].command(['PTTL', ip_key])
        if type(ttl) is not int or not 0 < ttl <= settings.window_ms:
            raise ValueError('Missing bounded TTL')
        report['atomic_fixture'] = {'independent_clients':3, 'simultaneous_attempts':3,
            'per_ip_limit':2, 'accepted':2, 'rejected':1, 'fresh_client_rejected':True, 'ip_ttl_ms':ttl}
    finally:
        for lease in active:
            await workers[0].release(lease)
    if await workers[0].command(['ZCARD', workers[0].leases_key]) != 0:
        raise ValueError('Lease release failed')
    # A separate short-lived fixture verifies actual server expiry, not a fake clock.
    expiry = Probe(replace(settings, namespace=settings.namespace+'-ttl', window_ms=1000, lease_ms=1000))
    await expiry.acquire(identity)
    await asyncio.sleep(1.25)
    expiry_key = expiry.prefix + 'ip:' + hashlib.sha256(identity.encode()).hexdigest()
    if await expiry.command(['PTTL', expiry_key]) != -2 or await expiry.command(['PTTL', expiry.leases_key]) != -2:
        raise ValueError('Fixture did not expire')
    renewed = await Probe(expiry.settings).acquire(identity)
    await expiry.release(renewed)
    ordered = sorted(times)
    report.update({'status':'passed', 'lease_release_verified':True, 'real_expiry_verified':True,
        'fresh_client_after_expiry_verified':True, 'command_observations':len(times),
        'command_latency_seconds':{'p50':round(statistics.median(times),4),
            'p95':round(ordered[math.ceil(.95*len(ordered))-1],4)},
        'limitations':['Isolated fixture parameters; no production visitor keys touched.',
            'Independent local REST clients sharing hosted Redis; not actual Vercel worker or HTTP routing validation.',
            'Local-to-Redis timing; deployment region and cold/warm HTTP latency remain unverified.']})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'status':'skipped: use --live',
            'script_sha256':hashlib.sha256(ACQUIRE_SCRIPT.encode()).hexdigest()}
    code=0
    if args.live:
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env.local')
        try:
            asyncio.run(check(report))
        except Exception as error:
            report.update({'status':'failed','error_type':type(error).__name__})
            code=1
    output=json.dumps(report,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output)
    print(output,end='')
    return code


if __name__=='__main__':
    raise SystemExit(main())
