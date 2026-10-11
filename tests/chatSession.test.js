import test from 'node:test';
import assert from 'node:assert/strict';
import { ChatSession, requestMessages } from '../src/lib/chatSession.js';

const ok = (reply = 'A documented answer.') => new Response(JSON.stringify({ reply, sources: ['project'] }));

test('default browser transport retains the global fetch receiver', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = function () {
    assert.equal(this, globalThis);
    return Promise.resolve(ok());
  };
  try {
    assert.equal((await new ChatSession().send('Question')).reply, 'A documented answer.');
  } finally {
    globalThis.fetch = original;
  }
});

test('12 turns plus an intervening failure stay bounded and contain only successful turns', async () => {
  const requests = [];
  let fail = false;
  const session = new ChatSession(async (_, options) => {
    requests.push(JSON.parse(options.body).messages);
    return fail ? new Response('unavailable', { status: 503 }) : ok();
  });
  for (let i = 0; i < 12; i++) {
    if (i === 6) {
      fail = true;
      await assert.rejects(session.send('Failed question'), error => error.status === 503);
      fail = false;
    }
    await session.send(`Question ${i}`);
  }
  assert.equal(requests.length, 13);
  assert.deepEqual(requests[0], [{ role: 'user', content: 'Question 0' }]);
  for (const messages of requests) {
    assert.ok(messages.length <= 19);
    assert.equal(messages.at(-1).role, 'user');
    assert.ok(messages.every((m, i) => m.role === (i % 2 ? 'assistant' : 'user')));
  }
  assert.ok(!requests.at(-1).some(m => m.content === 'Failed question'));
  assert.equal(session.history.length, 20);
});

test('request body also bounds UTF-8 bytes and preserves complete turns', () => {
  const history = Array.from({ length: 18 }, (_, i) => ({ role: i % 2 ? 'assistant' : 'user', content: '漢'.repeat(2000) }));
  const messages = requestMessages(history, 'Current question');
  assert.ok(new TextEncoder().encode(JSON.stringify({ messages })).length <= 32768);
  assert.equal(messages[0].role, 'user');
  assert.equal(messages.at(-1).content, 'Current question');
  assert.equal(history.length, 18);
  assert.throws(() => requestMessages([], 'x'.repeat(2001)));
});

test('429, 400, outage, timeout, malformed reply, HTML and network failure are errors without history', async () => {
  for (const [status, message] of [[429, /17 seconds/], [400, /rephrase/], [503, /unavailable/], [504, /too long/]]) {
    const session = new ChatSession(async () => new Response('error', { status, headers: { 'Retry-After': '17' } }));
    await assert.rejects(session.send('Question'), error => error.status === status && message.test(error.message));
    assert.deepEqual(session.history, []);
    assert.equal(session.active, null);
  }
  for (const response of ['<html>error</html>', '{"reply":null,"sources":[]}', '{"reply":"hi","sources":[123]}']) {
    const session = new ChatSession(async () => new Response(response));
    await assert.rejects(session.send('Question'));
    assert.deepEqual(session.history, []);
  }
  const session = new ChatSession(async () => { throw new TypeError('Failed to fetch'); });
  await assert.rejects(session.send('Question'), /Check your connection/);
});

test('deadline exits loading even when a transport ignores AbortSignal', async () => {
  const session = new ChatSession(() => new Promise(() => {}), 10);
  await assert.rejects(session.send('Question'), error => error.status === 504);
  assert.equal(session.active, null);
  assert.deepEqual(session.history, []);
});

test('close/reset cancel pending work and prevent late replies from entering the next chat', async () => {
  let resolve;
  const session = new ChatSession(() => new Promise(r => { resolve = r; }));
  const pending = session.send('Old question');
  session.reset();
  await assert.rejects(pending, /canceled/);
  session.fetchImpl = async () => ok('New answer');
  await session.send('New question');
  resolve(ok('Late answer'));
  await new Promise(r => setTimeout(r, 0));
  assert.deepEqual(session.history.map(m => m.content), ['New question', 'New answer']);
  session.reset();
  assert.deepEqual(session.history, []);
});

test('a policy refusal is an ordinary successful response, not an outage', async () => {
  const session = new ChatSession(async () => new Response(JSON.stringify({ reply: 'I can only answer questions about the portfolio.', sources: [] })));
  assert.equal((await session.send('Question')).sources.length, 0);
  assert.equal(session.history.length, 2);
});
