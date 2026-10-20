"""Dados sintéticos de armazenamento; não são notícias reais."""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evoa_news.storage import backup_database, restore_database, verify_backup, database_path


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.database = self.root / "operational.sqlite3"
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TABLE decisions(id INTEGER PRIMARY KEY, reason TEXT)")
            db.execute("INSERT INTO decisions(reason) VALUES (?)", ("Avaliação FICTÍCIA",))

    def backup(self):
        return backup_database(self.database, self.root / "backups")

    def test_round_trip_including_committed_wal(self):
        with sqlite3.connect(self.database) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("INSERT INTO decisions(reason) VALUES ('Segunda avaliação FICTÍCIA')")
            db.commit()
            manifest = self.backup()
        destination = self.root / "restored.sqlite3"
        result = restore_database(manifest, destination)
        self.assertEqual(result["tables"], {"decisions": 2})
        with sqlite3.connect(destination) as db:
            self.assertEqual(db.execute("SELECT reason FROM decisions WHERE id=1").fetchone()[0], "Avaliação FICTÍCIA")
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

    def test_versioned_backups_preserve_previous(self):
        first, second = self.backup(), self.backup()
        self.assertNotEqual(first, second)
        self.assertTrue(first.exists())
        self.assertEqual(verify_backup(first)[1]["tables"], {"decisions": 1})

    def test_restore_never_overwrites(self):
        original = self.database.read_bytes()
        with self.assertRaises(FileExistsError):
            restore_database(self.backup(), self.database)
        self.assertEqual(original, self.database.read_bytes())

    def test_missing_source_does_not_create_empty_database(self):
        missing = self.root / "missing.sqlite3"
        with self.assertRaises(FileNotFoundError):
            backup_database(missing, self.root / "backups")
        self.assertFalse(missing.exists())

    def test_corrupted_snapshot_is_rejected(self):
        manifest = self.backup()
        snapshot, _ = verify_backup(manifest)
        snapshot.write_bytes(b"FICTICIO corrupted")
        destination = self.root / "restored.sqlite3"
        with self.assertRaises(ValueError):
            restore_database(manifest, destination)
        self.assertFalse(destination.exists())

    def test_manifest_path_traversal_is_rejected(self):
        manifest = self.backup()
        data = json.loads(manifest.read_text())
        data["snapshot"] = "../operational.sqlite3"
        manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            verify_backup(manifest)

    def test_bad_source_is_not_backed_up(self):
        self.database.write_bytes(b"NOT A DATABASE")
        with self.assertRaises(sqlite3.DatabaseError):
            self.backup()
        self.assertEqual(list((self.root / "backups").iterdir()), [])

    def test_failed_restore_cleans_partial_file(self):
        manifest = self.backup()
        with patch("evoa_news.storage.os.link", side_effect=OSError("simulated error")):
            with self.assertRaises(OSError):
                restore_database(manifest, self.root / "restored.sqlite3")
        self.assertEqual(list(self.root.glob(".evoa-restore-*")), [])

    def test_environment_and_default_paths(self):
        with patch.dict(os.environ, {"EVOA_DATABASE": "/volume/evoa/history.sqlite3"}):
            self.assertEqual(database_path(), Path("/volume/evoa/history.sqlite3"))
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(database_path(), Path("data/history.sqlite3"))

    def test_cli_backup_verify_restore(self):
        def command(*args):
            return subprocess.run([sys.executable, "-m", "evoa_news.storage", *args], capture_output=True, text=True)
        with patch.dict(os.environ, {"EVOA_DATABASE": str(self.database), "EVOA_BACKUP_DIR": str(self.root / "cli-backups")}):
            result = command("backup")
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(result.stdout)["manifest"]
        result = command("verify", manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        destination = str(self.root / "cli-restored.sqlite3")
        result = command("restore", manifest, "--destination", destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["tables"], {"decisions": 1})
        self.assertEqual(command("restore", manifest, "--destination", destination).returncode, 1)

    def test_manifest_counts_are_verified(self):
        manifest = self.backup()
        data = json.loads(manifest.read_text())
        data["tables"]["decisions"] = 999
        manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            verify_backup(manifest)


if __name__ == "__main__":
    unittest.main()
