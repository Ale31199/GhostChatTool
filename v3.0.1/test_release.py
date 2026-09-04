"""Offline regression checks. All writes target TemporaryDirectory fixtures."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch as mock_patch

import ghostchat_patch as core
import ghostchat_watch as watch


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ghostchat-v3-tests-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'catalog.db'
        self.log = self.root / 'synthetic.log'
        with closing(sqlite3.connect(self.db)) as con, con:
            con.executescript('''
                CREATE TABLE local_thread_catalog (
                  host_id TEXT, thread_id TEXT, display_title TEXT,
                  source_kind TEXT, project_id TEXT, missing_candidate INTEGER,
                  source_recency_at REAL);
                CREATE TABLE local_thread_catalog_metadata(catalog_revision INTEGER);
                INSERT INTO local_thread_catalog_metadata VALUES(5);
                INSERT INTO local_thread_catalog VALUES
                  ('cloud','test-deleted','Disposable test','chatgpt',NULL,0,4),
                  ('cloud','test-keep','Keep test','chatgpt',NULL,1,3),
                  ('cloud','test-project','Project test','chatgpt','project',1,2),
                  ('local','test-work','Work test','codex',NULL,1,1);
            ''')
        values = dict(DB_DIR=self.root, DB_PATH=self.db,
                      BACKUP_DIR=self.root/'backups', PATCH_DIR=self.root/'state',
                      PATCH_LOG=self.root/'state'/'patch.log',
                      MANIFEST_DIR=self.root/'state'/'manifests')
        for name, value in values.items():
            handle = mock_patch.object(core, name, value)
            handle.start()
            self.addCleanup(handle.stop)
        for name, value in [('chatgpt_running', False), ('discover_log_roots', [self.root])]:
            handle = mock_patch.object(core, name, return_value=value)
            handle.start()
            self.addCleanup(handle.stop)

    def ids(self, db=None):
        with closing(sqlite3.connect(db or self.db)) as con, con:
            return {r[0] for r in con.execute('SELECT thread_id FROM local_thread_catalog')}

    def evidence(self, text):
        self.log.write_text(text, encoding='utf-8')
        with closing(sqlite3.connect(self.db)) as con, con:
            rows = core.fetch_cloud_catalog(con)
        return core.find_deleted_evidence(rows, [self.log])

    def test_versions(self):
        self.assertEqual(core.VERSION, '3.0.1')
        self.assertEqual(watch.VERSION, '3.0.1')

    def test_original_runtime_hashes(self):
        base = Path(__file__).resolve().parent
        expected = json.loads((base/'CORE_SHA256.json').read_text(encoding='utf-8'))
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((base/name).read_bytes()).hexdigest(), digest)

    def test_project_and_work_excluded_on_supported_schema(self):
        with closing(sqlite3.connect(self.db)) as con, con:
            self.assertEqual({r.thread_id for r in core.fetch_cloud_catalog(con)}, {'test-deleted', 'test-keep'})

    def test_missing_flag_and_generic_errors_not_proof(self):
        self.assertFalse(self.evidence('test-keep missing_candidate=1 404 conversation_not_loaded\n'))

    def test_marker_and_id_must_share_line(self):
        self.assertFalse(self.evidence('test-deleted\nconversation_deleted\n'))

    def test_unrelated_id_not_proof(self):
        self.assertFalse(self.evidence('other-id conversation_deleted\n'))

    def test_explicit_marker(self):
        self.assertEqual(set(self.evidence('test-deleted conversation_deleted\n')), {'test-deleted'})

    def test_alternative_marker(self):
        self.assertEqual(set(self.evidence('test-deleted conversation deleted\n')), {'test-deleted'})

    def test_watcher_same_line_gate(self):
        with closing(sqlite3.connect(self.db)) as con, con:
            rows = {r.thread_id: r for r in core.fetch_cloud_catalog(con)}
        self.assertFalse(watch.evidence_from_lines(rows, self.log, ['test-deleted\n', 'conversation_deleted\n']))
        self.assertEqual(set(watch.evidence_from_lines(rows, self.log, ['test-deleted conversation_deleted'])), {'test-deleted'})

    def test_dry_run_preserves_database_and_makes_no_backup(self):
        self.log.write_text('test-deleted conversation_deleted\n', encoding='utf-8')
        before = self.db.read_bytes()
        result = core.repair_once(dry_run=True)
        self.assertEqual(result['removed'], 0)
        self.assertEqual(len(result['confirmed']), 1)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertFalse(core.BACKUP_DIR.exists())

    def test_no_evidence_no_change(self):
        self.log.write_text('test-keep missing_candidate=1\n', encoding='utf-8')
        before = self.db.read_bytes()
        self.assertEqual(core.repair_once()['removed'], 0)
        self.assertEqual(self.db.read_bytes(), before)

    def test_targeted_repair_backup_manifest_revision_integrity(self):
        self.log.write_text('test-deleted conversation_deleted\n', encoding='utf-8')
        result = core.repair_once()
        self.assertEqual(result['removed'], 1)
        self.assertEqual(self.ids(), {'test-keep', 'test-project', 'test-work'})
        self.assertIn('test-deleted', self.ids(result['backup']))
        self.assertTrue(result['manifest'].is_file())
        with closing(sqlite3.connect(self.db)) as con, con:
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(con.execute('SELECT catalog_revision FROM local_thread_catalog_metadata').fetchone()[0], 6)

    def test_duplicate_id_rolls_back(self):
        with closing(sqlite3.connect(self.db)) as con, con:
            con.execute("INSERT INTO local_thread_catalog SELECT * FROM local_thread_catalog WHERE thread_id='test-deleted'")
        with closing(sqlite3.connect(self.db)) as con, con:
            with self.assertRaises(RuntimeError):
                core.delete_confirmed(con, ['test-deleted'])
            self.assertEqual(con.execute("SELECT count(*) FROM local_thread_catalog WHERE thread_id='test-deleted'").fetchone()[0], 2)

    def test_running_app_blocks_non_hot_repair(self):
        self.log.write_text('test-deleted conversation_deleted\n', encoding='utf-8')
        before = self.db.read_bytes()
        with mock_patch.object(core, 'chatgpt_running', return_value=True):
            with self.assertRaises(RuntimeError):
                core.repair_once(allow_running=False)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertFalse(core.BACKUP_DIR.exists())

    def test_restore_snapshot(self):
        self.log.write_text('test-deleted conversation_deleted\n', encoding='utf-8')
        with mock_patch.object(core, 'now_stamp', return_value='20000101-000000'):
            result = core.repair_once()
        with mock_patch.object(core, 'now_stamp', return_value='20000101-000001'):
            core.restore_backup(result['backup'])
        self.assertIn('test-deleted', self.ids())
        self.assertEqual(len(list(core.BACKUP_DIR.glob('*.db'))), 2)


if __name__ == '__main__':
    unittest.main()
