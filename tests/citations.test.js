import test from 'node:test';
import assert from 'node:assert/strict';
import { ChatSession } from '../src/lib/chatSession.js';

const citation = { label: 'S1', chunk_id: 'stable-chunk', source: 'cognisynth', project: 'CogniSynth',
  section: 'Architecture', subsection: '', document_version: 'a'.repeat(64), score: 0.812,
  excerpt: 'Neo4j stores the extracted research-paper knowledge graph.' };
const data = { reply: 'CogniSynth uses Neo4j. [S1]', sources: ['cognisynth'], citations: [citation] };
const sessionFor = value => new ChatSession(async () => new Response(JSON.stringify(value)));

test('source passages retain stable IDs, quote, score, version and inline labels', async () => {
  const session = sessionFor(data);
  const response = await session.send('What database does CogniSynth use?');
  assert.deepEqual(response.citations, [citation]);
  assert.deepEqual(session.history.at(-1), { role: 'assistant', content: data.reply });
  assert.equal(session.history.some(message => 'citations' in message), false);
});

test('bad citation metadata and mismatched references never enter history', async () => {
  const invalid = [
    { ...data, citations: null }, { ...data, citations: 'S1' }, { ...data, citations: [{ ...citation, label: 'S99' }] },
    { ...data, citations: [citation, citation] }, { ...data, reply: 'An answer [S2]' },
    { ...data, sources: ['different-document'] }, { ...data, citations: [{ ...citation, excerpt: 'short' }] },
    { ...data, citations: [{ ...citation, score: '0.8' }] }, { ...data, citations: [{ ...citation, chunk_id: '' }] },
    { ...data, citations: [{ ...citation, document_version: 123 }] },
  ];
  for (const value of invalid) {
    const session = sessionFor(value);
    await assert.rejects(session.send('Question'), error => error.status === 503);
    assert.equal(session.history.length, 0);
  }
});

test('legacy replies remain readable and abstentions have no claimed evidence', async () => {
  const response = await sessionFor({ reply: 'Legacy answer', sources: ['old-doc'] }).send('Question');
  assert.deepEqual(response.citations, []);
  assert.equal((await sessionFor({ reply: "I don't have specific documentation on that yet.", sources: [], citations: [] }).send('Unknown fact')).citations.length, 0);
});
