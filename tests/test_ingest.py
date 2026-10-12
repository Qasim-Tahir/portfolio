from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, patch

from qdrant_client.http.models import Distance, VectorParams
from scripts.check_qdrant import EMBED_MODEL, inspect_collection
from scripts.ingest import corpus_points, refresh, rollback
from scripts import ingest


class FakeQdrant:
    def __init__(self):
        self.collections = {'old': []}
        self.aliases = {'portfolio-live': 'old'}
        self.fail_batch = False
        self.bad_count = False
        self.bad_retrieval = False
        self.operations = []

    def get_aliases(self):
        return NS(aliases=[NS(alias_name=a, collection_name=t) for a, t in self.aliases.items()])

    def collection_exists(self, name):
        return name in self.collections

    def create_collection(self, collection_name, vectors_config):
        self.collections[collection_name] = []
        return True

    def upsert(self, collection_name, points, wait):
        assert wait is True
        if self.fail_batch:
            raise RuntimeError('Embedding or upload failed')
        self.collections[collection_name].extend(points)

    def create_payload_index(self, collection_name, field_name, field_schema, wait):
        assert field_name == 'project' and field_schema == 'keyword' and wait is True

    def get_collection(self, name):
        return NS(config=NS(params=NS(vectors={'content_vector': VectorParams(size=384, distance=Distance.COSINE)})))

    def count(self, collection_name, exact):
        return NS(count=0 if self.bad_count else len(self.collections[collection_name]))

    def scroll(self, collection_name, **kwargs):
        return self.collections[collection_name][:1], None

    def query_points(self, collection_name, **kwargs):
        return NS(points=[] if self.bad_retrieval else self.collections[collection_name][:1])

    def update_collection_aliases(self, change_aliases_operations):
        self.operations.append(change_aliases_operations)
        replacement = dict(self.aliases)
        for operation in change_aliases_operations:
            if hasattr(operation, 'delete_alias'):
                del replacement[operation.delete_alias.alias_name]
            else:
                replacement[operation.create_alias.alias_name] = operation.create_alias.collection_name
        self.aliases = replacement
        return True


class IngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        (self.directory / 'project.md').write_text('## Architecture\n' + 'A public project uses documented retrieval and generation. ' * 20)
        self.points = corpus_points(self.directory)

    def test_corpus_preflight_and_stable_ids(self):
        self.assertEqual([p.id for p in self.points], [p.id for p in corpus_points(self.directory)])
        self.assertTrue(all(p.payload['embedding_model'] == EMBED_MODEL for p in self.points))
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaisesRegex(ValueError, 'No Markdown'):
                corpus_points(empty)
        for content, message in [('', 'Empty document'), ('short', 'no usable chunks'), ('gsk_12345678901234567890', 'credential')]:
            (self.directory / 'project.md').write_text(content)
            with self.assertRaisesRegex(ValueError, message):
                corpus_points(self.directory)
        (self.directory / 'project.md').write_bytes(b'\xff')
        with self.assertRaises(UnicodeDecodeError):
            corpus_points(self.directory)

    def test_refresh_verifies_before_atomic_switch_and_rollback_retains_versions(self):
        client = FakeQdrant()
        client.collections['old'] = self.points
        version, previous = refresh(client, 'portfolio-live', self.points)
        self.assertEqual(previous, 'old')
        self.assertEqual(client.aliases['portfolio-live'], version)
        self.assertIn('old', client.collections)
        self.assertEqual(len(client.operations[0]), 2)
        self.assertEqual(rollback(client, 'portfolio-live', 'old'), version)
        self.assertEqual(client.aliases['portfolio-live'], 'old')
        self.assertIn(version, client.collections)

    def test_all_staging_failures_leave_live_alias_intact(self):
        for failure in ['fail_batch', 'bad_count', 'bad_retrieval']:
            with self.subTest(failure=failure):
                client = FakeQdrant()
                setattr(client, failure, True)
                with self.assertRaises((RuntimeError, ValueError)):
                    refresh(client, 'portfolio-live', self.points)
                self.assertEqual(client.aliases['portfolio-live'], 'old')
                self.assertEqual(client.operations, [])
                self.assertIn('old', client.collections)
        client = FakeQdrant()
        with self.assertRaises(ValueError):
            refresh(client, 'portfolio-live', [])
        self.assertEqual(list(client.collections), ['old'])

    def test_physical_name_collision_does_not_delete_or_create(self):
        client = FakeQdrant()
        with self.assertRaisesRegex(ValueError, 'physical collection'):
            refresh(client, 'old', self.points)
        self.assertEqual(list(client.collections), ['old'])

    def test_named_vector_inspection_and_missing_or_wrong_config(self):
        client = FakeQdrant()
        client.collections['old'] = self.points
        report = inspect_collection(client, 'old', require_model=True)
        self.assertEqual(report['dimensions'], 384)
        self.assertEqual(report['points'], len(self.points))
        for vectors in [VectorParams(size=384, distance=Distance.COSINE), {},
                        {'content_vector': VectorParams(size=768, distance=Distance.COSINE)}]:
            fake = MagicMock()
            fake.get_collection.return_value = NS(config=NS(params=NS(vectors=vectors)))
            with self.assertRaises(ValueError):
                inspect_collection(fake, 'old')

    def test_existing_repository_docs_pass_preflight_without_remote_calls(self):
        self.assertGreater(len(corpus_points(Path(__file__).resolve().parents[1] / 'docs')), 0)

    def test_failed_file_read_stops_before_remote_client_creation(self):
        (self.directory / 'project.md').write_bytes(b'\xff')
        with patch.object(ingest, 'load_dotenv'), patch.object(ingest, 'QdrantClient') as client, patch('sys.argv', ['ingest.py', '--docs', str(self.directory)]):
            with self.assertRaises(UnicodeDecodeError):
                ingest.main()
            client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
