#!/usr/bin/env python3
"""Merge all scrape JSON files into public/all_data.json for the dashboard."""

import json
import glob
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "public", "all_data.json")

SHOW_ORDER = [
    "Fri May 8 7PM",
    "Sat May 9 2PM",
    "Sat May 9 7PM",
    "Sun May 10 2PM",
    "Fri May 15 7PM",
    "Sat May 16 2PM",
    "Sat May 16 7PM",
    "Sun May 17 2PM",
]

SECTION_TOTALS = {
    "SEC-1": 84,
    "SEC-2": 81,
    "SEC-3": 87,
    "SEC-4": 87,
    "SEC-5": 81,
    "SEC-6": 84,
}

SECTION_ORDER = ["SEC-1", "SEC-2", "SEC-3", "SEC-4", "SEC-5", "SEC-6"]


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "scrape_*.json")))
    if not files:
        print("No scrape files found in", DATA_DIR)
        return

    combined = []

    for filepath in files:
        with open(filepath) as f:
            raw = json.load(f)

        scraped_at = raw["scraped_at"]
        stats = raw.get("stats", {})

        total_available = 0
        total_blocked = 0
        shows = {}

        for show_name in SHOW_ORDER:
            if show_name not in stats:
                continue
            show_data = stats[show_name]
            sections = show_data.get("sections", {})

            show_available = 0
            show_blocked = 0
            show_sections = {}

            for sec_id in SECTION_ORDER:
                if sec_id not in sections:
                    continue
                sec = sections[sec_id]
                avail = sec["available"]
                blocked = sec["blocked"]
                show_available += avail
                show_blocked += blocked
                show_sections[sec_id] = {
                    "available": avail,
                    "blocked": blocked,
                    "total": SECTION_TOTALS[sec_id],
                }

            total_available += show_available
            total_blocked += show_blocked

            shows[show_name] = {
                "available": show_available,
                "blocked": show_blocked,
                "total": show_available + show_blocked,
                "sections": show_sections,
            }

        combined.append({
            "scraped_at": scraped_at,
            "total_available": total_available,
            "total_blocked": total_blocked,
            "shows": shows,
        })

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Wrote {len(combined)} snapshots to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
