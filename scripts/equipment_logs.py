#!/usr/bin/env python3
"""Header, event-type distribution and sample rows for the equipment logs."""
from __future__ import annotations
import csv, json
from collections import Counter
from pathlib import Path

ROOT = Path("data/extracted")
OUT = Path("results"); OUT.mkdir(exist_ok=True)
report = {}
for path in sorted(ROOT.rglob("*.csv")):
    if path.name == "data_opcua.csv":
        continue
    with path.open(newline="", errors="replace") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames or []
        rows = list(rd)
    rep = {"rows": len(rows), "columns": cols, "sample": rows[:3]}
    low = {}
    for c in cols:
        vals = [r.get(c, "") for r in rows]
        uniq = Counter(vals)
        if len(uniq) <= 25:
            low[c] = dict(uniq.most_common(25))
    rep["low_cardinality_columns"] = low
    report[str(path.relative_to(ROOT))] = rep
    print(f"{path.name:32s} rows={len(rows):>7d} cols={cols[:6]}")
(OUT / "equipment_log_inventory.json").write_text(json.dumps(report, indent=1))
