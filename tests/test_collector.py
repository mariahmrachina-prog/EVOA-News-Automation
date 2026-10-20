"""Todas as notícias destes testes são FICTÍCIAS e usam example.org."""
import csv
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from evoa_news.collector import canonical_url, load_sources, run

NOW = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
SOURCE = {"name": "Fonte FICTÍCIA", "url": "https://example.org/rss", "category": "tecnologia", "trust": 90}


def item(title="Startup FICTÍCIA anuncia software", link="https://example.org/fiction", date="Tue, 20 Oct 2026 10:00:00 GMT"):
    pub = f"<pubDate>{date}</pubDate>" if date else ""
    return f"<item><title>{title}</title><link>{link}</link>{pub}<description>&lt;p&gt;Resumo FICTÍCIO de tecnologia&lt;/p&gt;</description></item>"


def feed(*items):
    return ("<rss version='2.0'><channel><title>Feed FICTÍCIO</title><link>https://example.org</link><description>Teste</description>" + "".join(items) + "</channel></rss>").encode()


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def collect(self, payload, sources=None, **kwargs):
        return run(sources or [SOURCE], self.root / "history.db", self.root / "out", now=NOW,
                   fetcher=lambda _: payload, **kwargs)

    def test_real_outputs_and_persistent_deduplication(self):
        first = self.collect(feed(item(), item(link="https://example.org/fiction?utm_source=x")))
        self.assertEqual(first["new_articles"], 1)
        self.assertEqual(first["sources"][0]["duplicates"], 1)
        folder = Path(first["output"])
        with (folder / "news.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter=";"))
        self.assertEqual(rows[0]["published_at"], "2026-10-20T10:00:00+00:00")
        self.assertEqual(rows[0]["summary"], "Resumo FICTÍCIO de tecnologia")
        self.assertTrue(0 <= int(rows[0]["relevance"]) <= 100)
        self.assertIn("https://example.org/fiction", (folder / "report.md").read_text())
        second = run([SOURCE], self.root / "history.db", self.root / "out",
                     now=datetime(2026, 10, 21, 9, tzinfo=timezone.utc), fetcher=lambda _: feed(item()))
        self.assertEqual(second["new_articles"], 0)
        self.assertNotEqual(first["output"], second["output"])
        with sqlite3.connect(self.root / "history.db") as db:
            self.assertEqual(db.execute("SELECT count(*) FROM runs").fetchone()[0], 2)

    def test_window_missing_and_future_publication(self):
        result = self.collect(feed(item("Antiga FICTÍCIA", "https://example.org/old", "Sun, 18 Oct 2026 10:00:00 GMT"),
                                   item("Futura FICTÍCIA", "https://example.org/future", "Wed, 21 Oct 2026 10:00:00 GMT"),
                                   item("Sem data FICTÍCIA", "https://example.org/unknown", None)))
        self.assertEqual(result["new_articles"], 1)
        report = (Path(result["output"]) / "report.md").read_text()
        self.assertIn("atualidade não confirmada", report)
        self.assertEqual(result["sources"][0]["ignored"], 2)

    def test_updated_is_not_publication(self):
        payload = b'''<feed xmlns="http://www.w3.org/2005/Atom"><title>FICTICIO</title><entry><title>AI FICTICIA</title><link href="https://example.org/atom"/><updated>2026-10-20T11:00:00Z</updated></entry></feed>'''
        result = self.collect(payload)
        self.assertEqual(result["new_articles"], 1)
        self.assertIn("Publicação: não informada", (Path(result["output"]) / "report.md").read_text())

    def test_source_failure_does_not_stop_healthy_feed(self):
        def fetcher(url):
            if "offline" in url:
                raise TimeoutError("Fonte FICTÍCIA indisponível")
            return feed(item())
        result = run([dict(SOURCE, url="https://example.org/offline"), SOURCE], self.root / "db", self.root / "out", now=NOW, fetcher=fetcher)
        self.assertEqual(result["sources"][0]["status"], "error")
        self.assertEqual(result["sources"][1]["status"], "ok")
        self.assertEqual(result["new_articles"], 1)
        self.assertIn("TimeoutError", json.dumps(result))

    def test_invalid_response_recorded(self):
        result = self.collect(b"<html>blocked</html>")
        self.assertEqual(result["sources"][0]["status"], "error")

    def test_syndicated_title_dedup(self):
        result = self.collect(feed(item(), item(link="https://example.org/syndicated")))
        self.assertEqual(result["new_articles"], 1)

    def test_csv_formula_protection(self):
        result = self.collect(feed(item("=FICTICIO(1)")))
        with (Path(result["output"]) / "news.csv").open(encoding="utf-8-sig", newline="") as stream:
            row = next(csv.DictReader(stream, delimiter=";"))
        self.assertEqual(row["title"], "'=FICTICIO(1)")

    def test_tracking_removed_but_identity_preserved(self):
        self.assertEqual(canonical_url("https://example.org/a?id=2&utm_source=x#fragment"), "https://example.org/a?id=2")
        with self.assertRaises(ValueError):
            canonical_url("javascript:alert(1)")

    def test_aggregator_never_fabricates_original(self):
        result = self.collect(feed(item()), [dict(SOURCE, aggregator=True)])
        with (Path(result["output"]) / "news.csv").open(encoding="utf-8-sig", newline="") as stream:
            self.assertEqual(next(csv.DictReader(stream, delimiter=";"))["original_link"], "")

    def test_freshness_and_trust_affect_ranking(self):
        result = self.collect(feed(item("AI FICTÍCIA antiga", "https://example.org/a", "Mon, 19 Oct 2026 13:00:00 GMT"),
                                   item("AI FICTÍCIA recente", "https://example.org/b")))
        with (Path(result["output"]) / "news.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter=";"))
        self.assertGreater(int(rows[0]["relevance"]), int(rows[1]["relevance"]))
        from evoa_news.collector import parse_article
        import feedparser
        entry = feedparser.parse(feed(item())).entries[0]
        self.assertGreater(parse_article(entry, SOURCE, NOW, 24)["relevance"], parse_article(entry, dict(SOURCE, trust=20), NOW, 24)["relevance"])

    def test_failed_export_does_not_consume_history(self):
        blocked = self.root / "blocked"
        blocked.write_text("Not a directory")
        with self.assertRaises(FileExistsError):
            run([SOURCE], self.root / "history.db", blocked, now=NOW, fetcher=lambda _: feed(item()))
        self.assertEqual(self.collect(feed(item()))["new_articles"], 1)

    def test_configuration_validation(self):
        path = self.root / "sources.json"
        path.write_text(json.dumps([dict(SOURCE, trust=101)]))
        with self.assertRaises(ValueError):
            load_sources(path)


if __name__ == "__main__":
    unittest.main()
