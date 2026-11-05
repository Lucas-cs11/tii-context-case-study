#!/usr/bin/env python3
"""Inventory OPC-UA and equipment logs of the four CONTEXT scenarios."""
from __future__ import annotations
import csv, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("data/extracted")
OUT = Path("results"); OUT.mkdir(exist_ok=True)
SCEN = {"ground_truth": "2020-07-20-1_8_g_8_n_ground_truth",
        "shuttle_dropout": "2020-07-20-3_2_g_1_n_5_g_8_n_shuttle_drop_out",
        "missing_parts": "2020-07-20-4_8_g_3_n_1_m_1_n_2_m_1_n_missing_parts",
        "missing_pressure": "2020-07-20-7-8_g_8_n_pressure"}
report = {}
for label, d in SCEN.items():
    base = ROOT / d
    rep = {"files": {}, "opcua": {}}
    for f in sorted(base.glob("*.csv")):
        with f.open(newline="", errors="replace") as fh:
            rd = csv.reader(fh)
            header = next(rd, [])
            rows = list(rd)
        rep["files"][f.name] = {"rows": len(rows), "columns": header}
    op = base / "data_opcua.csv"
    if op.exists():
        with op.open(newline="", errors="replace") as fh:
            rd = csv.DictReader(fh)
            cols = rd.fieldnames or []
            node_col = next((c for c in cols if c.lower() in ("nodeid", "node_id", "node")), None)
            time_col = next((c for c in cols if "time" in c.lower()), None)
            val_col = next((c for c in cols if c.lower() in ("value", "val", "newvalue")), None)
            nodes = defaultdict(Counter)
            n_rows = 0
            tmin = tmax = None
            for r in rd:
                n_rows += 1
                nid = r.get(node_col, "") if node_col else ""
                nodes[nid][r.get(val_col, "") if val_col else ""] += 1
                ts = r.get(time_col, "") if time_col else ""
                if ts:
                    tmin = ts if tmin is None or ts < tmin else tmin
                    tmax = ts if tmax is None or ts > tmax else tmax
            rep["opcua"] = {"rows": n_rows, "columns": cols, "node_column": node_col,
                            "time_column": time_col, "value_column": val_col,
                            "t_min": tmin, "t_max": tmax,
                            "unique_nodes": len(nodes),
                            "nodes": [{"nodeid": n, "count": sum(c.values()),
                                       "values": dict(c.most_common(6))}
                                      for n, c in sorted(nodes.items(), key=lambda kv: -sum(kv[1].values()))]}
    report[label] = rep
(OUT / "opcua_inventory.json").write_text(json.dumps(report, indent=1))
for label, rep in report.items():
    print(f"== {label}: opcua rows {rep['opcua'].get('rows')}, nodes {rep['opcua'].get('unique_nodes')}")
    for n in rep["opcua"].get("nodes", [])[:25]:
        print(f"   {n['count']:>7d}  {n['nodeid'][:90]}  values={list(n['values'])[:3]}")
