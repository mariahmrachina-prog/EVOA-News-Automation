"""Integração Google SIMULADA: nenhuma conta ou API real é acessada."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from evoa_news.google_drive import discover, upload_new, FOLDER
from evoa_news.sheets import panel_plan, read_panel


class HttpFailure(Exception):
    def __init__(self, status):
        self.resp = SimpleNamespace(status=status)


class Request:
    def __init__(self, callback):
        self.callback = callback
    def execute(self, **kwargs):
        return self.callback()


class FakeDrive:
    def __init__(self):
        self.remote = {"root": {"id": "root", "name": "Official", "mimeType": FOLDER}}
        self.created = 0
        self.allocated = 0
        self.timeout = False
        self.pages = {None: {"files": [{"id": "one", "name": "01 - Notícias Coletadas", "mimeType": FOLDER}], "nextPageToken": "two"},
                      "two": {"files": [{"id": "backup", "name": "06 - Backups", "mimeType": FOLDER}]}}
    def files(self):
        return self
    def get(self, fileId, **kwargs):
        def call():
            if fileId not in self.remote:
                raise HttpFailure(404)
            return self.remote[fileId]
        return Request(call)
    def list(self, q, pageToken=None, **kwargs):
        if "appProperties" in q:
            return Request(lambda: {"files": [{"id": v["id"]} for v in self.remote.values() if v.get("appProperties", {}).get("evoa_key", "never-match") in q]})
        return Request(lambda: self.pages[pageToken])
    def generateIds(self, **kwargs):
        self.allocated += 1
        identifier = "preallocated-" + str(self.allocated)
        return Request(lambda: {"ids": [identifier]})
    def create(self, body, **kwargs):
        def call():
            self.created += 1
            self.remote[body["id"]] = body
            if self.timeout:
                self.timeout = False
                raise TimeoutError("Resposta perdida após criação simulada")
            return {"id": body["id"]}
        return Request(call)


class GoogleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.file = self.root / "demo.txt"
        self.file.write_text("FICTICIO", encoding="utf-8")
        self.journal = self.root / "journal.sqlite3"
        self.service = FakeDrive()

    def upload(self, **kwargs):
        return upload_new(self.service, self.file, "backup", self.journal, media_factory=lambda: object(), **kwargs)

    def test_discovery_pagination_accents_missing_and_no_creation(self):
        result = discover(self.service, {"root_folder_id": "root", "folders": {"collected": "01 - Noticias Coletadas", "drafts": "02 - Noticias Redigidas"}})
        self.assertEqual(result["folders"]["collected"], "one")
        self.assertEqual(result["issues"]["drafts"]["error"], "missing")
        self.assertEqual(self.service.created, 0)

    def test_ambiguous_folder_not_silently_selected(self):
        self.service.pages["two"]["files"].append({"id": "other", "name": "01 - Noticias Coletadas", "mimeType": FOLDER})
        result = discover(self.service, {"root_folder_id": "root", "folders": {"collected": "01 - Noticias Coletadas"}})
        self.assertEqual(result["issues"]["collected"]["error"], "ambiguous")

    def test_approval_required_before_any_remote_write(self):
        with self.assertRaises(PermissionError):
            self.upload()
        self.assertEqual(self.service.created, 0)
        self.assertFalse(self.journal.exists())

    def test_incremental_repeat_does_not_duplicate(self):
        self.assertEqual(self.upload(approved=True)["status"], "uploaded")
        self.assertEqual(self.upload(approved=True)["status"], "already_present")
        self.assertEqual(self.service.created, 1)

    def test_timeout_reconciles_same_remote_id(self):
        self.service.timeout = True
        with self.assertRaises(TimeoutError):
            self.upload(approved=True)
        self.assertEqual(self.upload(approved=True)["status"], "already_present")
        self.assertEqual(self.service.created, 1)

    def test_recovery_after_local_journal_loss(self):
        self.upload(approved=True)
        self.journal.unlink()
        self.assertEqual(self.upload(approved=True)["status"], "already_present")
        self.assertEqual(self.service.created, 1)

    def test_remote_conflict_never_overwritten(self):
        self.upload(approved=True)
        self.service.remote["preallocated-1"]["appProperties"]["evoa_sha256"] = "changed"
        with self.assertRaises(ValueError):
            self.upload(approved=True)
        self.assertEqual(self.service.created, 1)

    def test_new_content_preserves_old_version(self):
        first = self.upload(approved=True)
        self.file.write_text("Outra versão FICTÍCIA", encoding="utf-8")
        second = self.upload(approved=True)
        self.assertNotEqual(first["id"], second["id"])
        self.assertIn(first["id"], self.service.remote)
        self.assertEqual(self.service.created, 2)

    def test_forbidden_is_not_treated_as_missing(self):
        self.service.get = lambda **kwargs: Request(lambda: (_ for _ in ()).throw(HttpFailure(403)))
        with self.assertRaises(HttpFailure):
            self.upload(approved=True)
        self.assertEqual(self.service.created, 0)

    def test_sheets_plan_and_read_only_adapter(self):
        self.assertEqual(panel_plan()["status"], "creation_requires_approval")
        self.assertIn("edited_text", panel_plan()["human_columns"])
        class FakeSheets:
            def spreadsheets(self): return self
            def values(self): return self
            def get(self, **kwargs): return Request(lambda: {"values": [["id", "title"], ["fiction", "FICTICIO"]]})
        self.assertEqual(len(read_panel(FakeSheets(), "fiction")), 2)


if __name__ == "__main__":
    unittest.main()
