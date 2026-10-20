"""API oficial: descoberta sem escrita e uploads novos com aprovação explícita."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sqlite3
import unicodedata
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly",
          "https://www.googleapis.com/auth/drive.file"]
FOLDER = "application/vnd.google-apps.folder"


def auth_directory() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "EVOANews" / "oauth"


def authenticate(client_file: Path, token_file: Path, *, interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    credentials = None
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        if not interactive:
            raise RuntimeError("Execute primeiro o comando auth na sua máquina Windows")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES, autogenerate_code_verifier=True)
        credentials = flow.run_local_server(host="localhost", port=0, open_browser=True,
                                            access_type="offline", prompt="consent")
    token_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Não imprimir o token. Diretório deve ser privado também por ACL no Windows.
    import tempfile
    fd, name = tempfile.mkstemp(dir=token_file.parent, prefix=".oauth-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(credentials.to_json())
        os.replace(name, token_file)
    finally:
        Path(name).unlink(missing_ok=True)
    return credentials


def drive_service(credentials):
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def discover(service, config: dict) -> dict:
    """Lista filhos da raiz; não cria nem renomeia pastas."""
    root = config["root_folder_id"]
    parent = service.files().get(fileId=root, fields="id,name,mimeType,trashed", supportsAllDrives=True).execute(num_retries=3)
    if parent.get("trashed") or parent["mimeType"] != FOLDER:
        raise ValueError("Raiz não é pasta ativa")
    children, page = [], None
    while True:
        result = service.files().list(q=f"'{_escape(root)}' in parents and trashed = false",
            fields="nextPageToken,files(id,name,mimeType)", pageToken=page,
            supportsAllDrives=True, includeItemsFromAllDrives=True, pageSize=100).execute(num_retries=3)
        children.extend(result.get("files", []))
        page = result.get("nextPageToken")
        if not page:
            break
    def normalized(name):
        return " ".join("".join(c for c in unicodedata.normalize("NFKD", name.casefold()) if not unicodedata.combining(c)).split())
    folders, issues = {}, {}
    for key, name in config["folders"].items():
        matches = [f["id"] for f in children if normalized(f["name"]) == normalized(name) and f["mimeType"] == FOLDER]
        if len(matches) == 1:
            folders[key] = matches[0]
        else:
            issues[key] = {"expected_name": name, "matches": matches, "error": "missing" if not matches else "ambiguous"}
    return {"root_folder_id": root, "folders": folders, "issues": issues,
            "spreadsheets": [f for f in children if f["mimeType"] == "application/vnd.google-apps.spreadsheet"]}


def _http_status(error):
    return getattr(getattr(error, "resp", None), "status", None)


def upload_new(service, file: Path, parent: str, journal: Path, *, approved=False, media_factory=None) -> dict:
    """Snapshot imutável. ID pré-alocado permite recuperar timeout sem duplicar.

    Use um único escritor; nunca atualiza ou remove arquivos existentes.
    """
    if not approved:
        raise PermissionError("Upload exige aprovação explícita; nada foi enviado")
    content = file.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    key = hashlib.sha256((parent + "\0" + file.name + "\0" + digest).encode()).hexdigest()
    journal.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(journal)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS uploads (key TEXT PRIMARY KEY, remote_id TEXT NOT NULL, status TEXT NOT NULL)")
        row = db.execute("SELECT remote_id,status FROM uploads WHERE key=?", (key,)).fetchone()
        if not row:
            matches = service.files().list(q=f"'{_escape(parent)}' in parents and trashed = false and appProperties has {{ key='evoa_key' and value='{key}' }}",
                fields="files(id)", pageSize=100, supportsAllDrives=True, includeItemsFromAllDrives=True).execute(num_retries=3).get("files", [])
            if len(matches) > 1:
                raise ValueError("Sincronização ambígua; resolver manualmente sem excluir arquivos")
            remote_id = matches[0]["id"] if matches else service.files().generateIds(count=1, space="drive").execute(num_retries=3)["ids"][0]
            db.execute("INSERT INTO uploads VALUES (?, ?, 'pending')", (key, remote_id))
            db.commit()  # Antes da escrita remota: conserva ID em resposta ambígua.
        else:
            remote_id = row[0]
        try:
            remote = service.files().get(fileId=remote_id, fields="id,parents,appProperties,trashed", supportsAllDrives=True).execute(num_retries=3)
        except Exception as error:
            if _http_status(error) != 404:
                raise
            remote = None
        if remote is not None:
            if remote.get("trashed") or parent not in remote.get("parents", []) or remote.get("appProperties", {}).get("evoa_sha256") != digest:
                raise ValueError("Conflito no ID remoto; nenhum arquivo foi alterado")
            status = "already_present"
        else:
            if media_factory is None:
                import io
                from googleapiclient.http import MediaIoBaseUpload
                media_factory = lambda: MediaIoBaseUpload(io.BytesIO(content), mimetype=mimetypes.guess_type(file.name)[0] or "application/octet-stream", resumable=False)
            service.files().create(body={"id": remote_id, "name": file.name, "parents": [parent],
                "appProperties": {"evoa_sha256": digest, "evoa_key": key}}, media_body=media_factory(),
                fields="id", supportsAllDrives=True).execute(num_retries=0)
            status = "uploaded"
        db.execute("UPDATE uploads SET status='complete' WHERE key=?", (key,))
        db.commit()
        return {"id": remote_id, "status": status, "sha256": digest}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Integração Google; descoberta é somente leitura")
    parser.add_argument("--config", type=Path, default=Path("config/google.json"))
    parser.add_argument("--client", type=Path, default=auth_directory() / "client_secret.json")
    parser.add_argument("--token", type=Path, default=auth_directory() / "token.json")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("auth")
    lookup = subs.add_parser("discover")
    lookup.add_argument("--output", type=Path, default=Path("data/google-folders.json"))
    upload = subs.add_parser("upload")
    upload.add_argument("file", type=Path)
    upload.add_argument("--kind", required=True)
    upload.add_argument("--journal", type=Path, default=Path("data/google-sync.sqlite3"))
    upload.add_argument("--approve-upload", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.command == "upload" and not args.approve_upload:
        parser.error("Revise arquivo e destino; --approve-upload só deve ser usado após aprovação")
    credentials = authenticate(args.client, args.token, interactive=args.command == "auth")
    if args.command == "auth":
        print("Autenticação concluída; credenciais armazenadas localmente, fora do Git.")
        return
    service = drive_service(credentials)
    if args.command == "discover":
        result = discover(service, config)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Redescobrir para validar pai real; não confiar cegamente em mapa editado.
        result = discover(service, config)
        if args.kind not in result["folders"]:
            parser.error("Subpasta ausente/ambígua; não será criada automaticamente")
        parent = result["folders"][args.kind]
        if args.kind == "backups":
            from .storage import verify_backup
            snapshot, _ = verify_backup(args.file)
            files = [snapshot, args.file]  # Manifesto enviado só após snapshot confirmado.
        else:
            if args.file.suffix.lower() in (".db", ".sqlite3", ".sqlite"):
                parser.error("Banco deve ser snapshot validado; use --kind backups com o manifesto")
            files = [args.file]
        for file in files:
            print(json.dumps(upload_new(service, file, parent, args.journal, approved=True)))


if __name__ == "__main__":
    main()
