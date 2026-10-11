import unittest
from scripts.evaluate_rag import load_cases, evidence_recall, percentile, summarize, ROOT
from scripts.sync_content import sync


class EvaluationTests(unittest.TestCase):
    def test_dataset_splits_do_not_overlap_and_cover_categories(self):
        tuning = load_cases(ROOT / 'evals/v1/tuning.jsonl')
        heldout = load_cases(ROOT / 'evals/v1/heldout.jsonl')
        self.assertFalse({r['id'] for r in tuning} & {r['id'] for r in heldout})
        for cases in (tuning, heldout):
            self.assertEqual({r['kind'] for r in cases}, {'fact','followup','unknown','unrelated','attack','social'})
        self.assertFalse(sync(check=True))

    def test_recall_requires_matching_source_and_passage(self):
        gold=[{'source':'ocr-summarizer','contains':'Scout'}]
        self.assertEqual(evidence_recall(gold,[{'source':'ocr-summarizer-technical','text':'Scout model'}]),1)
        self.assertEqual(evidence_recall(gold,[{'source':'other','text':'Scout model'}]),0)
        self.assertIsNone(evidence_recall([],[]))

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


if __name__ == '__main__':
    unittest.main()
