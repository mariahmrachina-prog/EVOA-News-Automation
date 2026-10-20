"""Notícias e links estritamente FICTÍCIOS; sem chamada a IA ou rede."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from evoa_news.drafting import prepare, validate_draft, export_queue
from evoa_news.feedback import record_decision, history, APPROVAL_REASONS, REJECTION_REASONS

ARTICLE = dict(title="Empresa FICTÍCIA apresenta produto FICTÍCIO", original_link="https://example.org/fiction",
               feed_link="https://example.org/fiction", published_at="2026-10-20T12:00:00+00:00", collected_at="2026-10-20T13:00:00+00:00",
               source="Fonte FICTÍCIA", category="tecnologia", relevance=1,
               summary="A empresa FICTÍCIA apresentou um produto de teste explicitamente FICTÍCIO, sem qualquer acontecimento real neste exemplo. A fonte FICTÍCIA descreve também um teste FICTÍCIO que será revisado por uma pessoa antes de qualquer uso.")


class DraftTests(unittest.TestCase):
    def test_low_score_gets_draft_and_evidence(self):
        result = prepare(ARTICLE)
        self.assertIsNotNone(result["draft"])
        self.assertEqual(result["provider"], "extractive")
        self.assertEqual(result["verification_status"], "Parcialmente sustentado")
        self.assertEqual(result["editorial_status"], "pending")
        for paragraph in result["draft"]["paragraphs"]:
            self.assertIn(paragraph, result["evidence"][0]["text"])
        self.assertLessEqual(len("\n\n".join(result["draft"]["paragraphs"])), 815)

    def test_short_summary_kept_without_speculative_draft(self):
        result = prepare(dict(ARTICLE, summary="Só título FICTÍCIO."))
        self.assertIsNone(result["draft"])
        self.assertEqual(result["verification_status"], "Evidência insuficiente")

    def test_structural_invalidity_is_rejected(self):
        draft = prepare(ARTICLE)["draft"]
        for changes in ({"paragraphs": ["only one"]}, {"paragraphs": ["x" * 814, "xx"]},
                        {"url": "https://example.org/wrong"}, {"cta": "Saiba mais"}, {"title": "No emoji"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_draft(dict(draft, **changes), ARTICLE["original_link"])

    def test_mock_ai_does_not_prove_facts(self):
        def fake(a, evidence):
            d = deepcopy(prepare(a)["draft"])
            d["evidence_ids"] = [evidence[0]["id"]]
            return d
        result = prepare(ARTICLE, provider="ollama", ai_writer=fake)
        self.assertIsNotNone(result["draft"])
        self.assertEqual(result["verification_status"], "Parcialmente sustentado")
        self.assertTrue(any("semanticamente" in x for x in result["limitations"]))

    def test_ai_error_is_explicit(self):
        def fail(*args): raise RuntimeError("Modelo FICTÍCIO indisponível")
        result = prepare(ARTICLE, provider="ollama", ai_writer=fail)
        self.assertIsNone(result["draft"])
        self.assertEqual(result["verification_status"], "Falha de verificação")

    def test_export_preserves_pending_items_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "out"
            export_queue([prepare(ARTICLE), prepare(dict(ARTICLE, summary="curto"))], dest)
            self.assertEqual(len(json.loads((dest / "queue.json").read_text())), 2)
            self.assertTrue((dest / "editorial.csv").is_file())
            with self.assertRaises(FileExistsError): export_queue([], dest)

    def test_feedback_idempotency_history_and_human_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "feedback.sqlite3"
            args = dict(event_id="e1", article_id="fiction", status="approved", reason=APPROVAL_REASONS[0],
                        original_draft={"title": "Original FICTÍCIO"}, edited_draft={"title": "Editado FICTÍCIO"})
            record_decision(path, **args)
            record_decision(path, **args)
            record_decision(path, **dict(args, event_id="e2", status="rejected", reason=REJECTION_REASONS[0]))
            events = history(path, "fiction")
            self.assertEqual(len(events), 2)
            self.assertNotEqual(events[0]["original_draft"], events[0]["edited_draft"])
            with self.assertRaises(ValueError): record_decision(path, **dict(args, comments="conflito"))


if __name__ == "__main__":
    unittest.main()
