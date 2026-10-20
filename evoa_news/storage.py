"""Backups SQLite consistentes. Nenhum upload ou sincronização implícita."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def database_path() -> Path:
    """Override explícito para volume persistente, sem alterar o padrão da v1."""
    return Path(os.environ.get("EVOA_DATABASE", "data/history.sqlite3")).expanduser()


def _readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Banco não encontrado: {path}")
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=30)


def _integrity(db: sqlite3.Connection) -> None:
    results = [row[0] for row in db.execute("PRAGMA integrity_check")]
    if results != ["ok"]:
        raise ValueError("Integridade SQLite inválida")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_info(path: Path) -> dict:
    with closing(_readonly(path)) as db:
        _integrity(db)
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        counts = {}
        for name in names:
            quoted = '"' + name.replace('"', '""') + '"'
            counts[name] = db.execute(f"SELECT count(*) FROM {quoted}").fetchone()[0]
    return {"sha256": _sha256(path), "bytes": path.stat().st_size, "tables": counts}


def _sync(path: Path) -> None:
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def backup_database(database: Path, directory: Path) -> Path:
    """Retorna manifesto de um snapshot novo; nunca modifica o banco original."""
    database, directory = Path(database).expanduser(), Path(directory).expanduser()
    # Não cria banco vazio quando a origem está ausente.
    source = _readonly(database)
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        name = f"history-{stamp}-{uuid.uuid4().hex}.sqlite3"
        snapshot = directory / name
        fd = os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        manifest = directory / (name + ".json")
        try:
            with closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)
                _integrity(target)
            _sync(snapshot)
            info = dict(format_version=1, created_at=datetime.now(timezone.utc).isoformat(),
                        snapshot=name, **_snapshot_info(snapshot))
            with manifest.open("x", encoding="utf-8") as stream:
                os.chmod(manifest, 0o600)
                json.dump(info, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            return manifest
        except BaseException:
            snapshot.unlink(missing_ok=True)
            manifest.unlink(missing_ok=True)
            raise
    finally:
        source.close()


def verify_backup(manifest: Path) -> tuple[Path, dict]:
    manifest = Path(manifest)
    if manifest.is_symlink():
        raise ValueError("Manifesto não pode ser link simbólico")
    info = json.loads(manifest.read_text(encoding="utf-8"))
    name = info["snapshot"]
    if info.get("format_version") != 1 or not isinstance(name, str) or Path(name).name != name or name in ("", ".", "..") or "/" in name or "\\" in name:
        raise ValueError("Manifesto inválido")
    snapshot = manifest.parent / name
    if snapshot.is_symlink():
        raise ValueError("Snapshot não pode ser link simbólico")
    if _sha256(snapshot) != info["sha256"]:
        raise ValueError("Checksum divergente; restauração cancelada")
    actual = _snapshot_info(snapshot)
    if any(actual[key] != info[key] for key in ("sha256", "bytes", "tables")):
        raise ValueError("Manifesto não corresponde ao snapshot")
    return snapshot, info


def restore_database(manifest: Path, destination: Path) -> dict:
    """Restaura em destino novo. Jamais substitui arquivo/banco existente."""
    snapshot, info = verify_backup(manifest)
    destination = Path(destination).expanduser()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destino já existe: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp_name = tempfile.mkstemp(prefix=".evoa-restore-", dir=destination.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with closing(_readonly(snapshot)) as source, closing(sqlite3.connect(temporary)) as target:
            source.backup(target)
            _integrity(target)
        restored = _snapshot_info(temporary)
        if restored["tables"] != info["tables"]:
            raise ValueError("Contagens da restauração divergem")
        _sync(temporary)
        # Publicação sem sobrescrita, mesmo que outro processo crie o destino.
        os.link(temporary, destination)
        return {"destination": str(destination), "integrity": "ok", "tables": restored["tables"]}
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup SQLite local; não envia dados ao Drive")
    subs = parser.add_subparsers(dest="command", required=True)
    backup = subs.add_parser("backup")
    backup.add_argument("--database", type=Path, default=database_path())
    backup.add_argument("--directory", type=Path, default=Path(os.environ.get("EVOA_BACKUP_DIR", "data/backups")))
    verify = subs.add_parser("verify")
    verify.add_argument("manifest", type=Path)
    restore = subs.add_parser("restore")
    restore.add_argument("manifest", type=Path)
    restore.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "backup":
            print(json.dumps({"manifest": str(backup_database(args.database, args.directory))}))
        elif args.command == "verify":
            _, info = verify_backup(args.manifest)
            print(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(restore_database(args.manifest, args.destination), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        parser.exit(1, f"Falha de armazenamento: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
