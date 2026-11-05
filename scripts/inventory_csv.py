#!/usr/bin/env python3
"""Header, row count, time range and missing-value inventory for every CSV."""
from __future__ import annotations
import csv, json
from collections import Counter
from pathlib import Path

ROOT = Path("data/extracted")
out = []
for path in sorted(ROOT.rglob("*.csv")):
    with path.open(newline="", errors="replace") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            out.append({"file": str(path.relative_to(ROOT)), "rows": 0, "empty": True}); continue
        rows = list(reader)
    times = []
    tcol = None
    for i, name in enumerate(header):
        low = name.lower()
        if "timestamp" in low or low in ("time", "ts", "datetime", "date"):
            tcol = i; break
    if tcol is not None:
        for r in rows:
            if len(r) > tcol:
                times.append(r[tcol])
        times = [t for t in times if t]
    missing = Counter()
    for r in rows:
        for i, name in enumerate(header):
            if i >= len(r) or r[i].strip() == "":
                missing[name] += 1
    out.append({"file": str(path.relative_to(ROOT)), "rows": len(rows), "columns": header,
                "timestamp_column": header[tcol] if tcol is not None else None,
                "time_min": min(times) if times else None, "time_max": max(times) if times else None,
                "missing": dict(missing)})
Path("results").mkdir(exist_ok=True)
Path("results/csv_inventory.json").write_text(json.dumps(out, indent=1))
print(f"csv files: {len(out)}")
for r in out:
    print(f"  {r['rows']:>8d} rows  {r['file']}")
