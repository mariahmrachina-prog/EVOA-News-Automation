"""Plano de painel e leitura oficial. Nenhuma criação/escrita implícita."""
import argparse
import json
from pathlib import Path

from .drafting import COLUMNS
from .google_drive import authenticate, auth_directory

HUMAN_COLUMNS = ["editorial_status", "decision_reason", "edited_text", "comments", "evaluated_at"]


def panel_plan():
    return {"title": "Painel Editorial EVOA News", "root_folder_id": "1in_94_e2fqQ878Xc3dG4vxq1BywnSSqM",
            "destination": "03 - Curadoria Editorial", "worksheet": "Noticias",
            "columns": COLUMNS, "human_columns": HUMAN_COLUMNS,
            "status": "creation_requires_approval", "input_mode": "RAW",
            "policy": "IDs estáveis; não sobrescrever colunas humanas; preservar versões e conflitos"}


def read_panel(service, spreadsheet_id):
    # API oficial Google Sheets v4, escopo drive.file para arquivo autorizado.
    return service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
        range="Noticias!A:U", valueRenderOption="UNFORMATTED_VALUE").execute(num_retries=3).get("values", [])


def main():
    parser = argparse.ArgumentParser(description="Plano local de Sheets ou leitura de planilha indicada")
    parser.add_argument("--spreadsheet-id")
    parser.add_argument("--output", type=Path, default=Path("data/sheets-plan.json"))
    parser.add_argument("--client", type=Path, default=auth_directory() / "client_secret.json")
    parser.add_argument("--token", type=Path, default=auth_directory() / "token.json")
    args = parser.parse_args()
    if args.spreadsheet_id:
        from googleapiclient.discovery import build
        service = build("sheets", "v4", credentials=authenticate(args.client, args.token), cache_discovery=False)
        result = {"spreadsheet_id": args.spreadsheet_id, "rows": read_panel(service, args.spreadsheet_id)}
    else:
        result = panel_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Resultado local: " + str(args.output))


if __name__ == "__main__":
    main()
