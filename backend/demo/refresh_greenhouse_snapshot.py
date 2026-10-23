"""Refresh the demo snapshot by running the real Greenhouse connector.

Usage (from backend/):
    YPP_INGEST_CONTACT="you@yourdomain.org" python -m demo.refresh_greenhouse_snapshot

The contact address is sent in the User-Agent so employers can reach us about their listings.
"""

import collections
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.ingestion.greenhouse import GreenhouseConnector

BOARDS = ["moniepoint", "alxafrica", "oafkenya", "oneacrefundglobal", "jumia", "impact"]
OUT = Path(__file__).with_name("greenhouse_snapshot.json")


def main() -> int:
    contact = os.environ.get("YPP_INGEST_CONTACT", "").strip()
    if not contact:
        print("Set YPP_INGEST_CONTACT to a real contact address before refreshing.", file=sys.stderr)
        return 2
    connector = GreenhouseConnector(user_agent=f"YPP-Ingest/0.1 ({contact})", min_interval_seconds=5.0)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    listings, boards = [], []
    try:
        for token in BOARDS:
            employer, drafts = connector.fetch_board(token)
            boards.append({"board_token": token, "employer": employer, "records": len(drafts)})
            listings.extend(d.to_dict() for d in drafts)
    finally:
        connector.close()

    status = collections.Counter(d["status"] for d in listings)
    doc = {
        "_notice": (
            "Snapshot of public Greenhouse Job Board API data for demonstration. Each listing links to the "
            "employer's original posting, which is the source of truth. Descriptions are the employer's public "
            "text with HTML removed. Refresh with demo/refresh_greenhouse_snapshot.py, do not edit by hand."
        ),
        "fetched_at": fetched_at,
        "boards": boards,
        "status_counts": dict(status),
        "listings": listings,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(listings)} records to {OUT.name}: {dict(status)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
