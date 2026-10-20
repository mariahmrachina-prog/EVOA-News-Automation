import argparse
import json
from pathlib import Path

from .collector import load_sources, run


def main():
    parser = argparse.ArgumentParser(description="Coletor RSS EVOA News; não publica conteúdo")
    parser.add_argument("--sources", type=Path, default=Path("config/sources.json"))
    parser.add_argument("--database", type=Path, default=Path("data/history.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--max-age-hours", type=float, default=24)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    if args.max_age_hours <= 0 or args.top < 1:
        parser.error("--max-age-hours deve ser positivo e --top >= 1")
    result = run(load_sources(args.sources), args.database, args.output,
                 max_age_hours=args.max_age_hours, top=args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if all(s["status"] == "error" for s in result["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
