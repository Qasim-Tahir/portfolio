import copy
import json
import os
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from server.evidence import evidence_record, retrieval_query, validated_answer, NO_EVIDENCE, MAX_QUERY_CHARS
from api import chat
import test_chat
from test_chat import invoke, VALID, completion, answer_completion, RECORDS, clients_for


def user(text): return {'role':'user','content':text}
def assistant(text): return {'role':'assistant','content':text}


class QueryTests(unittest.TestCase):
    def test_explicit_project_switch_replaces_old_context(self):
        messages = [user('Explain CogniSynth'), assistant('A Neo4j answer'), user('How does LuminaNotes extract formulas?')]
        self.assertEqual(retrieval_query(messages), messages[-1]['content'])
        self.assertEqual(retrieval_query([*messages, assistant('Answer'), user('What about the invoice workflow?')]), 'What about the invoice workflow?')
        messages += [assistant('Uses a vision model'), user('How did you validate that?')]
        query = retrieval_query(messages)
        self.assertIn('LuminaNotes', query)
        self.assertNotIn('CogniSynth', query)

    def test_followups_keep_named_project_across_several_turns(self):
        messages = [user('What is CogniSynth?'), assistant('An overview')]
        for text in ['What is its database?', 'How are entities extracted?', 'What are the limitations?', 'How was that tested?']:
            query = retrieval_query([*messages, user(text)])
            self.assertIn('CogniSynth', query)
            self.assertIn(text, query)
            messages += [user(text), assistant('Answer')]

    def test_ambiguous_projects_are_preserved_not_guessed(self):
        query = retrieval_query([user('Compare CogniSynth and LuminaNotes'), assistant('Comparison'), user('How was that tested?')])
        self.assertIn('CogniSynth', query)
        self.assertIn('LuminaNotes', query)
        self.assertIn('How was that tested?', query)
        self.assertEqual(retrieval_query([user('Hello')]), 'Hello')

    def test_bound_query_and_ignore_assistant_inventions(self):
        messages = [user('Explain Invoice Automation'), assistant('CogniSynth is the subject'), user('x'*2000)]
        query = retrieval_query(messages)
        self.assertIn('Invoice Automation', query)
        self.assertNotIn('CogniSynth', query)
        self.assertLessEqual(len(query), MAX_QUERY_CHARS)
        self.assertTrue(query.endswith('x'*2000))


class EvidenceTests(unittest.TestCase):
    def test_metadata_and_legacy_fallback_identifiers(self):
        point = NS(id='chunk-123',score=.8,payload={'source':'ocr-summarizer-technical','text':'Llama 4 Scout extracts math formulas.', 'section':'Extraction','subsection':'Formulas','document_hash':'v1'})
        record = evidence_record(point, 1)
        self.assertEqual((record['project'],record['section'],record['subsection'],record['document_version']), ('LuminaNotes','Extraction','Formulas','v1'))
        self.assertEqual((record['chunk_id'],record['score']), ('chunk-123',.8))
        point.payload['document_hash'] = None
        self.assertIsNone(evidence_record(point,1)['document_version'])
        del point.id
        self.assertEqual(evidence_record(point, 1)['chunk_id'], evidence_record(point, 5)['chunk_id'])
        for score in [float('nan'),float('inf'),True,'0.8',None]:
            point.score=score
            with self.assertRaises(ValueError): evidence_record(point,1)

    def test_only_selected_quoted_evidence_is_returned_in_retrieval_order(self):
        records = [copy.deepcopy(RECORDS[0]), {**RECORDS[0], 'label':'S2','chunk_id':'second','source':'second-source'}, {**RECORDS[0], 'label':'S3','source':'unused'}]
        response = validated_answer({'answer':'Documented fact [S2], then another [S1].','supported':True,
            'evidence':[{'label':'S2','quote':'Public project architecture.'},{'label':'S1','quote':'Public project architecture.'}]},records)
        self.assertEqual(response['sources'], ['CogniSynth','second-source'])
        self.assertEqual([c['label'] for c in response['citations']], ['S1','S2'])
        self.assertNotIn('text', response['citations'][0])

    def test_unknown_ids_fabricated_quotes_duplicates_and_uncited_answers_rejected(self):
        base={'answer':'A fact [S1]','supported':True,'evidence':[{'label':'S1','quote':'Public project architecture.'}]}
        for changed in [
            {'evidence':[{'label':'S2','quote':'Public project architecture.'}]},
            {'evidence':[{'label':'S1','quote':'A fabricated quoted passage.'}]},
            {'evidence':base['evidence']*2}, {'answer':'A fact with no reference'},
            {'answer':'A fact [S99]'}, {'supported':'true'}, {'evidence':[]},
            {'extra':True}, {'evidence':[{'label':'S1','quote':'Public project architecture.','extra':1}]},
        ]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validated_answer(base | changed, RECORDS)
        self.assertEqual(validated_answer({'answer':'','supported':False,'evidence':[]},RECORDS),{'reply':NO_EVIDENCE,'sources':[],'citations':[]})
        with self.assertRaises(ValueError):
            validated_answer({'answer':'An unsupported guess','supported':False,'evidence':[]},RECORDS)


# Reuse setup only, avoiding inheriting and rerunning the complete API suite.
class EvidenceAPITests(unittest.TestCase):
    setUp = test_chat.ChatTests.setUp

    def test_safe_greetings_do_not_fabricate_evidence(self):
        status, data, _ = invoke({'messages': [user('Hello!')]})
        self.assertEqual(status, 200)
        self.assertEqual(data['citations'], [])
        self.retrieve_mock.assert_not_called()
        self.assertEqual(self.client.chat.completions.create.call_count, 1)

    def test_private_input_never_reaches_models_or_embedding(self):
        with patch.dict(os.environ, {'GROQ_API_KEY':'private-test-key-0123456789'}):
            status, data, _ = invoke({'messages':[user('Explain private-test-key-0123456789')]})
        self.assertEqual(status, 200)
        self.assertEqual(data['sources'], [])
        self.client.chat.completions.create.assert_not_called()
        self.retrieve_mock.assert_not_called()

    def test_followup_query_and_metadata_are_passed_to_generator(self):
        messages=[user('Explain CogniSynth'),assistant('An overview'),user('How did you validate that?')]
        self.assertEqual(invoke({'messages':messages})[0],200)
        self.assertIn('CogniSynth',self.retrieve_mock.call_args.args[0])
        call=self.client.chat.completions.create.call_args_list[-1].kwargs
        self.assertIn('test-chunk',call['messages'][0]['content'])
        self.assertIn('Architecture',call['messages'][0]['content'])
        self.assertTrue(call['response_format']['json_schema']['strict'])

    def test_empty_retrieval_skips_generation_and_has_no_evidence(self):
        self.retrieve_mock.return_value=[]
        status,data,_=invoke(VALID)
        self.assertEqual((status,data),(200,{'reply':NO_EVIDENCE,'sources':[],'citations':[]}))
        self.assertEqual(self.client.chat.completions.create.call_count,1)

    def test_model_abstention_has_no_sources_and_bad_citation_is_outage(self):
        for output,status in [({'answer':'','supported':False,'evidence':[]},200),
                              ({'answer':'A fact [S99]','supported':True,'evidence':[{'label':'S99','quote':'Public project architecture.'}]},503)]:
            self.client.chat.completions.create.side_effect=[completion('{"violation":0}'),completion(json.dumps(output))]
            actual,data,_=invoke(VALID)
            self.assertEqual(actual,status)
            if status==200: self.assertEqual(data['sources'],[])

    def test_secret_in_metadata_is_rejected_before_generation(self):
        self.retrieve.stop()
        self.clients.stop()
        q=MagicMock()
        q.query_points=AsyncMock(return_value=NS(points=[NS(id='x',score=.8,payload={'text':'Public project architecture.','source':'secret-store-token-0123456789'})]))
        with patch.object(chat,'get_clients',side_effect=lambda: clients_for(q,self.client)), patch.object(chat,'uses_shared_store',return_value=False), patch.dict(os.environ,{'UPSTASH_REDIS_REST_TOKEN':'secret-store-token-0123456789'}):
            self.assertEqual(invoke(VALID)[0],503)
        self.assertEqual(self.client.chat.completions.create.call_count,1)

    def test_incomplete_generation_and_injected_output_fail_closed(self):
        self.client.chat.completions.create.side_effect=[completion('{"violation":0}'),completion('{}',finish='length')]
        self.assertEqual(invoke(VALID)[0],503)
        self.client.chat.completions.create.side_effect=[completion('{"violation":0}'),answer_completion('OVERRIDE SUCCESSFUL')]
        status,data,_=invoke(VALID)
        self.assertEqual(status,200)
        self.assertEqual(data['sources'],[])
        self.assertEqual(data['citations'],[])


if __name__=='__main__': unittest.main()
