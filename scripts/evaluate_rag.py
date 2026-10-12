"""Versioned offline regressions or opt-in, sequential live RAG evaluation."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.evidence import retrieval_query, NO_EVIDENCE
from server.prompts import GENERATION_MODEL, SAFEGUARD_MODEL, SYSTEM_PROMPT, SAFEGUARD_POLICY, GENERATION_MAX_TOKENS
from server.config import EMBED_MODEL, collection_name


def load_cases(path):
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Empty dataset or duplicate case IDs')
    for case in cases:
        if case['kind'] not in {'fact', 'followup', 'unknown', 'unrelated', 'attack', 'social'}:
            raise ValueError('Unknown evaluation category')
        if not case['messages'] or case['messages'][-1]['role'] != 'user':
            raise ValueError('Each case must end with a user question')
    return cases


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    # Nearest-rank percentile; no implied precision beyond a small fixed set.
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def evidence_recall(gold, records):
    if not gold:
        return None
    def matches(item, record):
        source = Path(record['source']).stem.removesuffix('-technical')
        phrases = item.get('contains_any', [item.get('contains', '')])
        return source == item['source'] and any(phrase and phrase.casefold() in record['text'].casefold() for phrase in phrases)
    return sum(any(matches(item, r) for r in records) for item in gold) / len(gold)


def ratio(values):
    return statistics.mean(values) if values else None


def summarize(rows, prices=None, reviews=None):
    completed = [r for r in rows if r['status'] == 'completed']
    answered = [r for r in completed if r['kind'] in ('fact', 'followup') and r.get('citations')]
    unknown = [r for r in completed if r['kind'] == 'unknown']
    facts = [r for r in completed if r['kind'] in ('fact', 'followup')]
    blocks = [r for r in completed if r['kind'] in ('attack', 'unrelated')]
    times = [r['elapsed_seconds'] for r in completed if not r.get('deterministic')]
    cost = 0
    usage_complete = True
    usage_calls = 0
    for r in rows:
        for call in r.get('usage', []):
            rate = (prices or {}).get('models', {}).get(call['model'])
            if not rate or call['input_tokens'] is None or call['output_tokens'] is None:
                usage_complete = False
                continue
            usage_calls += 1
            cost += (call['input_tokens'] * rate['input_usd_per_million'] + call['output_tokens'] * rate['output_usd_per_million']) / 1_000_000
    if any(r['status'] == 'failed' for r in rows):
        usage_complete = False  # failures may have unknown billable usage
    semantic = reviews.get('cases', {}) if reviews else {}
    answer_reviews = [semantic[r['id']] for r in answered if r['id'] in semantic]
    for review in answer_reviews:
        if any(type(review.get(key)) is not bool for key in ('supported_answer', 'citation_supported')):
            raise ValueError('Semantic review labels must be booleans')
    all_answered_reviewed = len(answer_reviews) == len(answered) and bool(answered)
    quoted_citations = [c for r in answered for c in r.get('citations', [])]
    return {
        'attempted_cases':len(rows), 'completed_cases':len(completed), 'failed_cases':len(rows)-len(completed),
        'answered_fact_cases':len(answered), 'completed_fact_cases':len(facts),
        'completed_unknown_cases':len(unknown), 'completed_attack_unrelated_cases':len(blocks),
        'retrieval_recall_at_5':ratio([r['retrieval_recall'] for r in facts if r.get('retrieval_attempted', True) and r.get('retrieval_recall') is not None]),
        'fact_retrieval_attempts':sum(r.get('retrieval_attempted', bool(r.get('retrieved'))) for r in facts),
        'end_to_end_gold_evidence_rate':ratio([r['retrieval_recall'] for r in facts if r.get('retrieval_recall') is not None]),
        'baseline_followup_recall_at_5':ratio([r['baseline_recall'] for r in facts if r.get('baseline_recall') is not None]),
        'contextual_followup_recall_at_5':ratio([r['retrieval_recall'] for r in facts if r['kind']=='followup' and r.get('retrieval_attempted', True) and r.get('retrieval_recall') is not None]),
        'gold_answer_text_check_rate':ratio([r['gold_answer_checks_pass'] for r in facts]),
        'false_refusal_rate':ratio([r.get('reply') in (NO_EVIDENCE, "I can only answer questions about Qasim's portfolio.") for r in facts]),
        'unknown_abstention_rate':ratio([r.get('reply') in (NO_EVIDENCE, "I can only answer questions about Qasim's portfolio.") and not r.get('citations') for r in unknown]),
        'attack_unrelated_refusal_rate':ratio([r.get('reply') in (NO_EVIDENCE, "I can only answer questions about Qasim's portfolio.") and not r.get('citations') for r in blocks]),
        'quote_provenance_rate':ratio([r.get('quote_provenance_pass',False) for r in answered]),
        'supported_answer_rate':ratio([r['supported_answer'] for r in answer_reviews]) if all_answered_reviewed else None,
        'semantic_citation_accuracy':ratio([r['citation_supported'] for r in answer_reviews]) if all_answered_reviewed else None,
        'semantic_reviewed_answers':len(answer_reviews), 'selected_citations':len(quoted_citations),
        'successful_provider_pipeline_latency_seconds':{'sample_size':len(times),'p50':percentile(times,.5),'p95':percentile(times,.95)},
        'successful_answer_latency_seconds':{'sample_size':len(answered),'p50':percentile([r['elapsed_seconds'] for r in answered],.5),'p95':percentile([r['elapsed_seconds'] for r in answered],.95)},
        'first_pipeline_observation_seconds':times[0] if times else None,
        'subsequent_pipeline_latency_seconds':{'sample_size':max(0,len(times)-1),'p50':percentile(times[1:],.5),'p95':percentile(times[1:],.95)},
        'llm_cost_estimate_usd':round(cost,8) if usage_calls else None,
        'llm_cost_per_answered_fact_usd':round(cost/len(answered),8) if usage_calls and answered else None,
        'cost_usage_complete':usage_complete and bool(usage_calls),
        'cost_scope':'Published Groq token-rate estimate across observed calls, including refusals; excludes Qdrant, Redis and hosting. Not a billed total.',
    }


def lexical_records(query, points):
    # A controlled, provider-free retrieval fixture, not cloud embeddings.
    terms = set(re.findall(r'\w+', query.casefold())) - {'the','is','what','how','a','of','it','its','which','does','in','for','to','and'}
    ranked = sorted(points, key=lambda p: (-len(terms & set(re.findall(r'\w+', (p.payload['project']+' '+p.payload['text']).casefold()))), str(p.id)))[:5]
    return [{'source':p.payload['source'],'text':p.payload['text']} for p in ranked]


def offline(cases):
    from scripts.ingest import corpus_points
    points = corpus_points(ROOT / 'docs')
    rows=[]
    for case in cases:
        query=retrieval_query(case['messages'])
        records=lexical_records(query,points)
        rows.append({'id':case['id'],'kind':case['kind'],'query_characters':len(query),
            'lexical_fixture_recall':evidence_recall(case['gold_evidence'],records),
            'baseline_lexical_fixture_recall':evidence_recall(case['gold_evidence'],lexical_records(case['messages'][-1]['content'],points)),
            'status':'fixture_checked'})
    return rows


async def live(cases, delay, stop_on_error):
    from api import chat
    rows=[]
    for index,case in enumerate(cases):
        observed_records=[]
        usage=[]
        row={'id':case['id'],'kind':case['kind'],'status':'failed','usage':usage,'retrieval_attempted':False}
        def observe(stage,value):
            if stage=='retrieval':
                row['retrieval_attempted']=True
                observed_records.extend(value)
            elif stage=='validation_failure':
                row['validation_failure']=value
            else:
                counts=getattr(value,'usage',None)
                usage.append({'stage':stage,'model':SAFEGUARD_MODEL if stage=='safeguard' else GENERATION_MODEL,
                    'input_tokens':getattr(counts,'prompt_tokens',None),'output_tokens':getattr(counts,'completion_tokens',None),
                    'finish_reason':getattr(value.choices[0],'finish_reason',None) if getattr(value,'choices',None) else None})
        start=time.monotonic()
        try:
            messages=chat.validate_messages({'messages':case['messages']})
            deterministic=any(chat.is_injection_attempt(m['content']) or chat.contains_private_value(m['content']) for m in messages)
            row['deterministic']=deterministic
            if deterministic:
                result={'reply':chat.REFUSAL,'sources':[],'citations':[]}
            else:
                async with chat.get_clients() as (q,g):
                    # Baseline comparison is a separate bounded retrieval call,
                    # excluded from the production-pipeline latency observation.
                    if case['kind']=='followup':
                        baseline_start=time.monotonic()
                        async with asyncio.timeout(chat.PROVIDER_TIMEOUT):
                            old=await chat.retrieve(messages[-1]['content'],chat.PROVIDER_TIMEOUT,client=q)
                        row['baseline_recall']=evidence_recall(case['gold_evidence'],old)
                        row['baseline_elapsed_seconds']=round(time.monotonic()-baseline_start,4)
                        start=time.monotonic()
                    async with asyncio.timeout(chat.REQUEST_BUDGET):
                        result=await chat.answer(messages,q,g,start+chat.REQUEST_BUDGET,observe)
            row.update(result)
            row['status']='completed'
            row['quote_provenance_pass']=all(any(c['chunk_id']==r['chunk_id'] and c['excerpt'] in r['text'] for r in observed_records) for c in result.get('citations',[]))
            row['gold_answer_checks_pass']=bool(result.get('citations')) and all(s.casefold() in result['reply'].casefold() for s in case['answer_checks'])
        except Exception as error:
            row.update({'error_type':type(error).__name__,'http_status':getattr(error,'status_code',None)})
            response=getattr(error,'response',None)
            if response is not None:
                allowed=('retry-after','x-ratelimit-limit-requests','x-ratelimit-limit-tokens','x-ratelimit-remaining-requests','x-ratelimit-remaining-tokens','x-ratelimit-reset-requests','x-ratelimit-reset-tokens')
                row['rate_headers']={name:response.headers[name][:64] for name in allowed if name in response.headers}
        row['elapsed_seconds']=round(time.monotonic()-start,4)
        row['retrieval_recall']=evidence_recall(case['gold_evidence'],observed_records)
        # Only screened, public metadata/scores are saved, never private endpoint URLs.
        row['retrieved']=[{k:r[k] for k in ('chunk_id','source','section','score','document_version')} for r in observed_records]
        rows.append(row)
        print(json.dumps({'case':row['id'],'status':row['status'],'elapsed_seconds':row['elapsed_seconds']}),flush=True)
        if row['status']=='failed' and stop_on_error:
            break
        if index<len(cases)-1:
            await asyncio.sleep(delay)
    return rows


async def remote_manifest():
    from api import chat
    async with chat.get_clients() as (q, _):
        async with asyncio.timeout(12):
            points, offset = await q.scroll(collection_name=collection_name(), limit=1000, with_payload=True, with_vectors=False)
            info = await q.get_collection(collection_name())
            aliases = await q.get_aliases()
    versions = {}
    for point in points:
        p = point.payload or {}
        versions.setdefault(p.get('source', 'unknown'), set()).add(p.get('document_hash'))
    return {'collection':collection_name(),'target':next((a.collection_name for a in aliases.aliases if a.alias_name == collection_name()), collection_name()),
        'point_count':info.points_count,'scanned_points':len(points),'scan_complete':offset is None,
        'document_versions':{source:sorted(v, key=lambda x: x or '') for source,v in versions.items()}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--dataset-version',choices=['v1','v2'],default='v1')
    parser.add_argument('--split',choices=['tuning','heldout'],default='heldout')
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--delay',type=float,default=3,help='Seconds between sequential live cases')
    parser.add_argument('--continue-on-error',action='store_true',help='Default stops at the first provider error')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reviews',type=Path,help='Qualitative labels tied to the exact result digest')
    parser.add_argument('--summarize',type=Path,help='Summarize an existing live report without provider requests')
    args=parser.parse_args()
    if not 1<=args.limit<=100 or not 0<=args.delay<=60:
        parser.error('limit must be 1..100; delay must be 0..60')
    prices=json.loads((ROOT/'evals/v1/prices.json').read_text())
    reviews=json.loads(args.reviews.read_text()) if args.reviews else None
    if args.summarize:
        report=json.loads(args.summarize.read_text())
        if reviews and reviews.get('results_sha256')!=hashlib.sha256(args.summarize.read_bytes()).hexdigest():
            raise ValueError('Review labels belong to a different result file')
        report['metrics']=summarize(report['cases'],prices,reviews)
        if reviews: report['semantic_review']={k:v for k,v in reviews.items() if k!='cases'}
    else:
        dataset=ROOT/f'evals/{args.dataset_version}/{args.split}.jsonl'
        cases=load_cases(dataset)[:args.limit]
        revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
        git=revision.stdout.strip() if revision.returncode==0 else None
        dirty=subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True) if git else None
        code_paths=[ROOT/'api/chat.py', *sorted((ROOT/'server').glob('*.py')), ROOT/'scripts/evaluate_rag.py', ROOT/'scripts/ingest.py']
        report={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'mode':'live' if args.live else 'offline_fixture',
            'split':args.split,'dataset_version':args.dataset_version,'dataset_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(), 'git_revision':git,
            'working_tree_has_changes':bool(dirty.stdout) if dirty is not None else None,
            'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
            'corpus_documents':{p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'docs').glob('*.md'))},
            'configuration':{'generation_model':GENERATION_MODEL,'safeguard_model':SAFEGUARD_MODEL,'embedding_model':EMBED_MODEL,'generation_max_tokens':GENERATION_MAX_TOKENS,'safeguard_max_tokens':1024,'top_k':5,'score_threshold':None,
                'prompt_sha256':hashlib.sha256((SYSTEM_PROMPT+SAFEGUARD_POLICY).encode()).hexdigest(),'groq_sdk':version('groq'),'qdrant_sdk':version('qdrant-client')},
            'requested_cases':len(cases),'latency_scope':'Local Python pipeline, excluding baseline retrieval comparison; not deployed Vercel latency. First request creates new clients; subsequent requests also create clients. Provider cache/cold state cannot be controlled.',
            'limitations':['Semantic citation accuracy is reviewed at answer level: every selected citation must support the answer.','Small fixed question set; not a general quality or security guarantee.','Gold text checks and quote membership do not prove semantic correctness.','No threshold or prompt tuning on heldout cases.','Live mode skips HTTP/quota guards; those are separately regression-tested.'], 'price_snapshot':prices}
        if args.live:
            from dotenv import load_dotenv
            load_dotenv(ROOT/'.env.local')
            os.environ.setdefault('FRONTEND_URL','http://localhost:5173')
            report['configuration']['collection']=collection_name()
            try:
                report['remote_corpus']=asyncio.run(remote_manifest())
                report['cases']=asyncio.run(live(cases,args.delay,not args.continue_on_error))
            except Exception as error:
                # Preflight errors may contain private endpoint/response data.
                report['preflight_error']={'error_type':type(error).__name__,'http_status':getattr(error,'status_code',None)}
                report['cases']=[]
            report['metrics']=summarize(report['cases'],prices)
        else:
            report['cases']=offline(cases)
            report['metrics']={'fixture_cases':len(cases),'live_answer_quality':None,'live_latency':None,'live_cost':None,
                'note':'Lexical fixture checks exercise bounded query construction and dataset/corpus compatibility. They are not provider-backed quality measurements.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(report['metrics'],indent=2))
    return int(args.live and (len(report['cases'])<report.get('requested_cases',0) or any(r['status']=='failed' for r in report['cases']) or 'preflight_error' in report))


if __name__=='__main__':
    raise SystemExit(main())
