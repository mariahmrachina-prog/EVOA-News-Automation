from __future__ import annotations

import calendar
import csv
import hashlib
import html
import json
import re
import sqlite3
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import feedparser

UTC = timezone.utc
TOPICS = {
    "inteligência artificial": ("artificial intelligence", "inteligencia artificial", " ai ", "machine learning", "openai", "llm"),
    "startups": ("startup", "venture capital", "funding", "empreendedor", "investimento"),
    "tecnologia": ("technology", "tecnologia", "software", "chip", "cyber", "inovacao", "innovation"),
    "negócios": ("business", "negocio", "economia", "market", "mercado", "empresa"),
}
FIELDS = ["title", "source", "original_link", "feed_link", "published_at", "category", "summary", "relevance", "justification", "collected_at"]


def plain(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value))).strip()


def normalized(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        raise ValueError("Link HTTP(S) inválido")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(sorted(query)), ""))


def title_key(title: str) -> str:
    return hashlib.sha256(re.sub(r"\W+", " ", normalized(title)).strip().encode()).hexdigest()


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "EVOA-News/1.0 (RSS reader)", "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(request, timeout=25) as response:
        data = response.read(5_000_001)
        if len(data) > 5_000_000:
            raise ValueError("Feed excede limite de 5 MB")
        return data


def load_sources(path: Path) -> list[dict]:
    sources = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(sources, list) or not sources:
        raise ValueError("Configure ao menos uma fonte")
    for source in sources:
        canonical_url(source["url"])
        if not source.get("name") or not source.get("category") or not 0 <= source["trust"] <= 100:
            raise ValueError("Fonte inválida: nome, categoria e trust entre 0 e 100 são obrigatórios")
    return sources


def parse_article(entry, source: dict, now: datetime, max_age_hours: float) -> dict | None:
    title = plain(entry.get("title", ""))
    if not title or not entry.get("link"):
        return None
    link = canonical_url(entry.link)
    # updated não substitui published: atualização não prova publicação recente.
    date = entry.get("published_parsed")
    published = datetime.fromtimestamp(calendar.timegm(date), UTC) if date else None
    age = (now - published).total_seconds() / 3600 if published else None
    if age is not None and (age < 0 or age > max_age_hours):
        return None
    summary = plain(entry.get("summary", ""))[:2000]
    text = " " + normalized(title + " " + summary) + " "
    category = next((name for name, keywords in TOPICS.items() if any(k in text for k in keywords)), source["category"])
    matched = any(k in text for words in TOPICS.values() for k in words)
    audience = 35 if matched else 20
    freshness = round(40 * max(0, 1 - age / max_age_hours)) if age is not None else 0
    reliability = round(source["trust"] * .25)
    score = min(100, freshness + audience + reliability)
    timing = f"publicada há {age:.1f} h" if age is not None else "data de publicação ausente; atualidade não confirmada"
    reason = f"{timing}; afinidade temática {audience}/35; confiabilidade editorial configurada {source['trust']}/100; atualidade {freshness}/40"
    # Agregadores não fornecem necessariamente o link original; não o inventar.
    return dict(title=title, source=source["name"], original_link="" if source.get("aggregator") else link,
                feed_link=link, published_at=published.isoformat() if published else "", category=category,
                summary=summary, relevance=score, justification=reason, collected_at=now.isoformat())


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS articles (url TEXT PRIMARY KEY, title_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, collected_at TEXT NOT NULL, result TEXT NOT NULL)")
    return db


def safe_cell(value):
    # Impede execução de fórmulas quando a planilha abre conteúdo de terceiros.
    return "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value


def md(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", plain(value))


def run(sources: list[dict], db_path: Path, output: Path, *, now: datetime | None = None,
        fetcher=fetch, max_age_hours: float = 24, top: int = 20) -> dict:
    now = now or datetime.now(UTC)
    if now.tzinfo is None or max_age_hours <= 0 or top < 1:
        raise ValueError("Use data com fuso, janela positiva e top >= 1")
    now = now.astimezone(UTC)
    articles, statuses = [], []
    db = connect(db_path)
    try:
        for source in sources:
            status = {"source": source["name"], "url": source["url"], "status": "ok", "read": 0, "new": 0, "duplicates": 0, "ignored": 0}
            try:
                feed = feedparser.parse(fetcher(source["url"]))
                if not feed.get("version"):
                    raise ValueError("Resposta não é RSS/Atom reconhecido")
                if feed.bozo:
                    raise ValueError(f"RSS/Atom malformado: {feed.bozo_exception}")
                status["read"] = len(feed.entries)
                for entry in feed.entries:
                    try:
                        article = parse_article(entry, source, now, max_age_hours)
                    except (ValueError, OverflowError, TypeError):
                        article = None
                    if article is None:
                        status["ignored"] += 1
                        continue
                    cursor = db.execute("INSERT OR IGNORE INTO articles VALUES (?, ?, ?)",
                                        (article["feed_link"], title_key(article["title"]), json.dumps(article, ensure_ascii=False)))
                    if cursor.rowcount:
                        articles.append(article)
                        status["new"] += 1
                    else:
                        status["duplicates"] += 1
            except sqlite3.Error:
                raise
            except Exception as error:
                status.update(status="error", error=f"{type(error).__name__}: {error}")
            statuses.append(status)
        articles.sort(key=lambda a: (-a["relevance"], a["title"]))
        # Diretório único por execução; a repetição não apaga relatórios anteriores.
        output.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix=now.strftime("%Y-%m-%dT%H%M%SZ-"), dir=output))
        with (folder / "news.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter=";")
            writer.writeheader()
            writer.writerows({k: safe_cell(v) for k, v in a.items()} for a in articles)
        report = [f"# EVOA News — {now:%Y-%m-%d} (UTC)", "", "Rascunho de curadoria: revisão humana obrigatória. Nenhuma publicação automática.",
                  "Datas abaixo representam publicação, não a data do acontecimento. Resumos são trechos do RSS, sem redação por IA.",
                  f"Janela: {max_age_hours:g} h. Itens sem data podem aparecer com atualidade não confirmada. Apenas itens novos no histórico.", ""]
        for a in articles[:top]:
            url = a["original_link"] or a["feed_link"]
            report.extend([f"## {md(a['title'])}", f"- Fonte: {md(a['source'])} | Categoria: {md(a['category'])} | Pontuação: {a['relevance']}/100",
                           f"- Publicação: {a['published_at'] or 'não informada'}", f"- Link {'original' if a['original_link'] else 'do agregador (original não confirmado)'}: <{url.replace('>', '%3E').replace('<', '%3C')}>",
                           f"- Seleção: {md(a['justification'])}", "", md(a["summary"]) or "Resumo não fornecido pelo RSS.", ""])
        if not articles:
            report.extend(["Nenhuma notícia nova elegível nesta execução.", ""])
        report.append("## Estado das fontes")
        for status in statuses:
            report.append(f"- {md(status['source'])}: {status['status']}; lidas={status['read']}, novas={status['new']}, duplicadas={status['duplicates']}, ignoradas={status['ignored']}. {md(status.get('error', ''))}")
        (folder / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        result = {"collected_at": now.isoformat(), "new_articles": len(articles), "sources": statuses, "output": str(folder)}
        (folder / "status.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        db.execute("INSERT INTO runs(collected_at, result) VALUES (?, ?)", (now.isoformat(), json.dumps(result, ensure_ascii=False)))
        db.commit()
        return result
    finally:
        db.close()
