import unittest
from scripts.evaluate_rag import load_cases, evidence_recall, percentile, summarize, ROOT
from scripts.sync_content import sync
from server.evidence import NO_EVIDENCE


class EvaluationTests(unittest.TestCase):
    def test_dataset_splits_do_not_overlap_and_cover_categories(self):
        for version in ('v1','v2'):
            tuning = load_cases(ROOT / f'evals/{version}/tuning.jsonl')
            heldout = load_cases(ROOT / f'evals/{version}/heldout.jsonl')
            self.assertFalse({r['id'] for r in tuning} & {r['id'] for r in heldout})
            self.assertFalse({str(r['messages']) for r in tuning} & {str(r['messages']) for r in heldout})
            for cases in (tuning, heldout):
                self.assertEqual({r['kind'] for r in cases}, {'fact','followup','unknown','unrelated','attack','social'})
        self.assertFalse(sync(check=True))

    def test_recall_requires_matching_source_and_passage(self):
        gold=[{'source':'ocr-summarizer','contains':'Scout'}]
        self.assertEqual(evidence_recall(gold,[{'source':'ocr-summarizer-technical','text':'Scout model'}]),1)
        self.assertEqual(evidence_recall(gold,[{'source':'other','text':'Scout model'}]),0)
        self.assertIsNone(evidence_recall([],[]))
        aliases=[{'source':'ocr-summarizer','contains_any':['Llama 4 Scout','llama-4-scout']}]
        self.assertEqual(evidence_recall(aliases,[{'source':'ocr-summarizer','text':'meta-llama/llama-4-scout-17b-16e-instruct'}]),1)

    def test_versioned_gold_evidence_exists_in_the_indexable_corpus(self):
        from scripts.ingest import corpus_points
        records=[point.payload for point in corpus_points(ROOT/'docs')]
        for version in ('v1','v2'):
            for split in ('tuning','heldout'):
                for case in load_cases(ROOT/f'evals/{version}/{split}.jsonl'):
                    if case['gold_evidence']:
                        with self.subTest(version=version,split=split,id=case['id']):
                            self.assertEqual(evidence_recall(case['gold_evidence'],records),1)

    def test_provider_errors_are_not_answer_latency_or_zero_cost(self):
        rows=[{'id':'H1','kind':'fact','status':'failed','elapsed_seconds':.1,'usage':[]}]
        summary=summarize(rows)
        self.assertEqual(summary['failed_cases'],1)
        self.assertIsNone(summary['successful_provider_pipeline_latency_seconds']['p50'])
        self.assertIsNone(summary['llm_cost_per_answered_fact_usd'])
        self.assertFalse(summary['cost_usage_complete'])
        self.assertIsNone(summary['supported_answer_rate'])

    def test_semantic_quality_requires_review_of_every_answer(self):
        rows=[{'id':'H1','kind':'fact','status':'completed','elapsed_seconds':1,'usage':[],
               'citations':[{'label':'S1'}],'reply':'Correct name, wrong relationship',
               'gold_answer_checks_pass':True,'quote_provenance_pass':True,'retrieval_recall':1}]
        self.assertIsNone(summarize(rows)['semantic_citation_accuracy'])
        result=summarize(rows,reviews={'cases':{'H1':{'supported_answer':False,'citation_supported':False}}})
        self.assertEqual(result['supported_answer_rate'],0)
        self.assertEqual(result['quote_provenance_rate'],1)
        self.assertEqual(percentile([4,1,3,2],.95),4)
        self.assertIsNone(percentile([], .5))

    def test_policy_refusal_is_not_a_retrieval_attempt(self):
        base={'kind':'followup','status':'completed','elapsed_seconds':1,'usage':[],
              'citations':[],'gold_answer_checks_pass':False,'baseline_recall':1}
        rows=[base|{'id':'blocked','reply':"I can only answer questions about Qasim's portfolio.",
                    'retrieval_attempted':False,'retrieval_recall':0},
              base|{'id':'retrieved','reply':NO_EVIDENCE,'retrieval_attempted':True,'retrieval_recall':1}]
        result=summarize(rows)
        self.assertEqual(result['contextual_followup_recall_at_5'],1)
        self.assertEqual(result['end_to_end_gold_evidence_rate'],.5)
        self.assertEqual(result['fact_retrieval_attempts'],1)


if __name__ == '__main__':
    unittest.main()
