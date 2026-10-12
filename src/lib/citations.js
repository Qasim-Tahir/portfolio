// Validate the public evidence contract before rendering provider-backed data.
export function validateCitations(data) {
  const citations = data.citations === undefined ? [] : data.citations;
  if (!Array.isArray(citations) || citations.length > 5) throw new Error('Invalid citations');
  const labels = new Set();
  for (const citation of citations) {
    if (!citation || typeof citation !== 'object' || Array.isArray(citation)
        || !/^S[1-5]$/.test(citation.label) || labels.has(citation.label)
        || !['source', 'project', 'section', 'subsection'].every(key => typeof citation[key] === 'string' && citation[key].length <= 200)
        || typeof citation.chunk_id !== 'string' || !citation.chunk_id || citation.chunk_id.length > 128
        || !(citation.document_version === null || (typeof citation.document_version === 'string' && citation.document_version.length <= 200))
        || !Number.isFinite(citation.score) || typeof citation.score !== 'number'
        || typeof citation.excerpt !== 'string' || citation.excerpt.trim().length < 20 || citation.excerpt.length > 600
        || !data.sources.includes(citation.source)) {
      throw new Error('Invalid citation record');
    }
    labels.add(citation.label);
  }
  if (citations.length) {
    const inline = new Set([...data.reply.matchAll(/\[(S[0-9]+)\]/g)].map(match => match[1]));
    if (inline.size !== labels.size || [...inline].some(label => !labels.has(label))) throw new Error('Citation references do not match');
  }
  return citations;
}
