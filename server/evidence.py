"""Bound follow-up queries and validate citations against retrieved passages."""
import hashlib
import json
import math
import re

def strict_json(text):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Invalid JSON constant")

    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=invalid_constant)


PROJECT_ALIASES = {
    'CogniSynth': ('cognisynth', 'cogni synth'),
    'LuminaNotes': ('luminanotes', 'lumina notes', 'ocr summarizer', 'ocr project', 'ocr-summarizer', 'lecture notes'),
    'Invoice Automation': ('invoice automation', 'invoice project', 'invoice workflow', 'invoice pipeline', 'invoice extraction'),
    'Islamic Source Finder': ('islamic source finder', 'islamicsourcefinder', 'islamic-source-finder'),
    'AI Portfolio Engine': ('portfolio engine', 'portfolio chatbot', 'portfolio assistant', 'portfolio rag', 'this chatbot', 'this portfolio', 'this assistant'),
}
SOURCE_PROJECTS = {
    'cognisynth': 'CogniSynth', 'ocr-summarizer': 'LuminaNotes',
    'invoice-automation': 'Invoice Automation', 'islamic-source-finder': 'Islamic Source Finder',
    'portfolio-rag': 'AI Portfolio Engine', 'about': 'Qasim Tahir',
}
NO_EVIDENCE = "I don't have specific documentation on that yet."
MAX_QUERY_CHARS = 2800


def named_projects(text):
    return [name for name, aliases in PROJECT_ALIASES.items()
            if any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', text, re.I) for alias in aliases)]


def retrieval_query(messages):
    current = messages[-1]['content']
    # A new explicitly named project replaces prior context. Assistant messages
    # cannot select a project: they are untrusted and may contain invented facts.
    if named_projects(current) or len(messages) == 1:
        return current[:MAX_QUERY_CHARS]
    previous_users = [m['content'] for m in messages[:-1] if m['role'] == 'user'][-9:]
    project_context = next((text for text in reversed(previous_users) if named_projects(text)), None)
    preceding = previous_users[-1] if previous_users else ''
    parts = []
    if project_context:
        # Preserve multiple names rather than guessing which one "that" means.
        parts.append('Previously discussed projects: ' + ', '.join(named_projects(project_context)))
    if preceding:
        parts.append('Previous question: ' + preceding[:500])
    parts.append('Current question: ' + current)
    return '\n'.join(parts)[:MAX_QUERY_CHARS]


def text_metadata(payload, key, default='', limit=200):
    value = payload.get(key, default)
    if value is None:
        value = default
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError('Invalid evidence metadata')
    return value


def evidence_record(point, index):
    payload = point.payload or {}
    text = payload.get('text')
    if not isinstance(text, str) or not text.strip() or len(text) > 10_000:
        raise ValueError('Invalid retrieved passage')
    source = text_metadata(payload, 'source', 'unknown')
    section = text_metadata(payload, 'section')
    subsection = text_metadata(payload, 'subsection')
    project = text_metadata(payload, 'project', SOURCE_PROJECTS.get(source.removesuffix('-technical'), source))
    version = text_metadata(payload, 'document_hash') or None
    score = getattr(point, 'score', None)
    if type(score) not in (int, float) or not math.isfinite(score):
        raise ValueError('Invalid retrieval score')
    identifier = getattr(point, 'id', None)
    if identifier is None:
        # Compatibility for legacy fixtures/documents lacking a point ID.
        identifier = hashlib.sha256(json.dumps([source, section, subsection, text]).encode()).hexdigest()
    if type(identifier) not in (str, int) or not 1 <= len(str(identifier)) <= 128:
        raise ValueError('Invalid chunk identifier')
    return {'label': f'S{index}', 'chunk_id': str(identifier), 'source': source,
            'project': project, 'section': section, 'subsection': subsection,
            'document_version': version, 'score': float(score), 'text': text}


def generation_format():
    return {'type': 'json_schema', 'json_schema': {
        'name': 'portfolio_answer', 'strict': True,
        'schema': {'type': 'object', 'additionalProperties': False,
            'properties': {
                'answer': {'type': 'string'}, 'supported': {'type': 'boolean'},
                'evidence': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
                    'properties': {'label': {'type': 'string'}, 'quote': {'type': 'string'}},
                    'required': ['label', 'quote']}},
            }, 'required': ['answer', 'supported', 'evidence']}}}


def validated_answer(data, records):
    """Validate identities, inline references and exact quotes, not entailment."""
    if (not isinstance(data, dict) or set(data) != {'answer', 'supported', 'evidence'}
            or type(data['supported']) is not bool or not isinstance(data['answer'], str)
            or not isinstance(data['evidence'], list)):
        raise ValueError('Invalid answer schema')
    answer, selected = data['answer'], data['evidence']
    if not data['supported']:
        if answer or selected:
            raise ValueError('Unsupported answer must have no claims or evidence')
        return {'reply': NO_EVIDENCE, 'sources': [], 'citations': []}
    if not answer.strip() or len(answer) > 6000 or not 1 <= len(selected) <= 5:
        raise ValueError('Invalid supported answer')
    by_label = {record['label']: record for record in records}
    citations = {}
    for entry in selected:
        if not isinstance(entry, dict) or set(entry) != {'label', 'quote'}:
            raise ValueError('Invalid citation schema')
        label, quote = entry['label'], entry['quote']
        if (not isinstance(label, str) or label not in by_label or label in citations
                or not isinstance(quote, str) or len(quote.strip()) < 20 or len(quote) > 600
                or quote not in by_label[label]['text']):
            raise ValueError('Citation must quote the retrieved passage exactly')
        record = by_label[label]
        citations[label] = {key: value for key, value in record.items() if key != 'text'} | {'excerpt': quote}
    inline = set(re.findall(r'\[S([0-9]+)\]', answer))
    if {'S' + number for number in inline} != set(citations):
        raise ValueError('Inline references and selected evidence must match')
    # Preserve retrieval order even if the model lists labels in reverse order.
    ordered = [citations[record['label']] for record in records if record['label'] in citations]
    sources = list(dict.fromkeys(citation['source'] for citation in ordered))
    return {'reply': answer, 'sources': sources, 'citations': ordered}
