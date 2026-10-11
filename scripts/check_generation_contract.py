"""Opt-in, single-request Groq schema check with a public fixture. No retrieval."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Make one provider request using configured Groq credentials')
    parser.add_argument('--output', type=Path, help='Optional redacted JSON result path')
    args = parser.parse_args()
    report = {'kind':'public-fixture generation contract smoke', 'fixture_version':1,
              'checked_at':datetime.now(timezone.utc).isoformat(), 'provider_request_attempted':False}
    code = 0
    if not args.live:
        report['status'] = 'skipped: use --live to opt in'
    else:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env.local')
        from server.prompts import SYSTEM_PROMPT, GENERATION_MODEL
        from server.evidence import generation_format, validated_answer, strict_json
        model = GENERATION_MODEL
        text = 'Qdrant Cloud stores document chunks and serves semantic similarity queries for the portfolio assistant.'
        record = {'label':'S1','chunk_id':'public-contract-fixture','source':'portfolio-rag',
                  'project':'AI Portfolio Engine','section':'Architecture','subsection':'',
                  'document_version':None,'score':0.8,'text':text}
        report.update({'model':model,'groq_sdk_version':version('groq'),
                       'fixture_sha256':hashlib.sha256(text.encode()).hexdigest(),
                       'max_completion_tokens':1024,'timeout_seconds':8,'max_retries':0})
        if not os.getenv('GROQ_API_KEY'):
            report['status'], code = 'skipped: no configured Groq key', 2
        else:
            client = Groq(api_key=os.environ['GROQ_API_KEY'], timeout=8, max_retries=0)
            start = time.monotonic()
            try:
                report['provider_request_attempted'] = True
                response = client.chat.completions.create(model=model,
                    messages=[{'role':'system','content':SYSTEM_PROMPT.format(context=json.dumps([record]))},
                              {'role':'user','content':'What does Qdrant do in the portfolio assistant?'}],
                    response_format=generation_format(), max_completion_tokens=1024, temperature=0.3)
                choice = response.choices[0]
                report['finish_reason'] = choice.finish_reason
                result = validated_answer(strict_json(choice.message.content), [record])
                if choice.finish_reason != 'stop' or not result['citations']:
                    raise ValueError('Incomplete or unsupported fixture answer')
                report.update({'status':'passed','citation_count':len(result['citations']),
                               'input_tokens':response.usage.prompt_tokens,'output_tokens':response.usage.completion_tokens})
            except Exception as error:
                # Provider exception strings/bodies can expose request data.
                report.update({'status':'failed','error_type':type(error).__name__,
                               'http_status':getattr(error,'status_code',None)})
                code = 1
            finally:
                report['elapsed_seconds'] = round(time.monotonic()-start,3)
                client.close()
    output = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    print(output, end='')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
