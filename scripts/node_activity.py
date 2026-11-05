#!/usr/bin/env python3
"""Per-NodeId activity statistics for the four CONTEXT scenarios.

A NodeId is only a candidate event if it actually changes state; the initial
appearance of a static variable is not an event.
"""
from __future__ import annotations
import csv, gzip, json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path("data/extracted")
OUT = Path("results"); OUT.mkdir(exist_ok=True)
SCEN = {"ground_truth": "2020-07-20-1_8_g_8_n_ground_truth",
        "shuttle_dropout": "2020-07-20-3_2_g_1_n_5_g_8_n_shuttle_drop_out",
        "missing_parts": "2020-07-20-4_8_g_3_n_1_m_1_n_2_m_1_n_missing_parts",
        "missing_pressure": "2020-07-20-7-8_g_8_n_pressure"}


def station_of(nodeid: str):
    m = re.search(r"Station\s*(\d+)", nodeid)
    return f"Station {m.group(1)}" if m else "other"


rows_out = []
summary = {}
for label, d in SCEN.items():
    stats = {}
    with (ROOT / d / "data_opcua.csv").open(newline="", errors="replace") as fh:
        rd = csv.DictReader(fh)
        for row in rd:
            nid = row["nodeid"]
            val = row["value"]
            ts = row["date"]
            s = stats.get(nid)
            if s is None:
                stats[nid] = {"count": 1, "values": {val}, "transitions": 0,
                              "first": ts, "last": ts, "prev": val, "bool_toggles": 0,
                              "numeric": None}
                continue
            s["count"] += 1
            if val != s["prev"]:
                s["transitions"] += 1
                if s["prev"] in ("True", "False") and val in ("True", "False"):
                    s["bool_toggles"] += 1
                s["prev"] = val
            if len(s["values"]) < 40:
                s["values"].add(val)
            if ts < s["first"]:
                s["first"] = ts
            if ts > s["last"]:
                s["last"] = ts
    actives = {n: s for n, s in stats.items() if s["transitions"] > 0}
    summary[label] = {"nodes_total": len(stats), "nodes_with_transitions": len(actives),
                      "rows": sum(s["count"] for s in stats.values())}
    for nid, s in stats.items():
        rows_out.append({"scenario": label, "nodeid": nid, "station": station_of(nid),
                         "count": s["count"], "distinct_values": len(s["values"]),
                         "transitions": s["transitions"], "bool_toggles": s["bool_toggles"],
                         "first": s["first"], "last": s["last"],
                         "sample_values": "|".join(sorted(s["values"])[:5])})
    print(label, "nodes", len(stats), "with transitions", len(actives))
with gzip.open(OUT / "node_activity_inventory.csv.gz", "wt", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
    w.writeheader(); w.writerows(rows_out)
(OUT / "node_activity_summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
