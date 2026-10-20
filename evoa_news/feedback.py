"""Registro local de decisões/edições. Não implica treinamento automático."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

APPROVAL_REASONS = ["Relevante para empresários e lideranças", "Grande impacto no mercado", "Novidade tecnológica significativa",
                    "Aplicação prática interessante", "Tema estratégico para a EVOA", "Informação exclusiva ou pouco explorada"]
REJECTION_REASONS = ["Pouco relevante para o público", "Notícia repetida", "Informação superficial", "Tema excessivamente técnico",
                    "Notícia desatualizada", "Fonte pouco confiável", "Assunto já abordado na newsletter"]


def record_decision(database: Path, *, event_id: str, article_id: str, status: str, reason: str,
                    original_draft: dict, edited_draft: dict | None = None, comments="", ranker_version="base-v1"):
    if status not in ("approved", "rejected", "pending"):
        raise ValueError("Status inválido")
    allowed = APPROVAL_REASONS if status == "approved" else REJECTION_REASONS
    if status != "pending" and reason not in allowed:
        raise ValueError("Motivo padronizado obrigatório")
    if not event_id or not article_id:
        raise ValueError("IDs obrigatórios")
    payload = dict(article_id=article_id, status=status, reason=reason, original_draft=original_draft,
                   edited_draft=edited_draft, comments=comments, ranker_version=ranker_version)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    database.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(database)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS editorial_events(event_id TEXT PRIMARY KEY, article_id TEXT NOT NULL, evaluated_at TEXT NOT NULL, payload TEXT NOT NULL)")
        existing = db.execute("SELECT payload FROM editorial_events WHERE event_id=?", (event_id,)).fetchone()
        if existing and existing[0] != encoded:
            raise ValueError("ID de evento já usado com conteúdo diferente")
        db.execute("INSERT OR IGNORE INTO editorial_events VALUES (?, ?, ?, ?)",
                   (event_id, article_id, datetime.now(timezone.utc).isoformat(), encoded))
        db.commit()
    finally:
        db.close()


def history(database: Path, article_id: str):
    if not database.is_file():
        return []
    db = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return [dict(event_id=r[0], evaluated_at=r[1], **json.loads(r[2])) for r in db.execute(
            "SELECT event_id,evaluated_at,payload FROM editorial_events WHERE article_id=? ORDER BY rowid", (article_id,))]
    finally:
        db.close()
