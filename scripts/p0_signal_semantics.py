#!/usr/bin/env python3
"""P0: empirical semantics of S7-GRAPH style signals (.T/.U, Taktmerker, busy flags).

For every targeted NodeId we extract the full value sequence and classify it from the
data (dtype, monotonicity, resets, dwell times, periodicity), not from its name.
"""
from __future__ import annotations
import csv, json, re, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path("data/extracted")
OUT = Path("results"); OUT.mkdir(exist_ok=True)
GT = ROOT / "2020-07-20-1_8_g_8_n_ground_truth" / "data_opcua.csv"
PATTERNS = ["Ablaufkette_iDB.Init", "AblaufketteShuttle_DB.Init", "Taktmerker",
            "SQ_BUSY", "SA_BUSY", "Step127", "Shuttletueren", "Programm wird ausgefuehrt",
            "Ist-Druck", "Ventil", "LiftBit", "Zustandsautomat", "lnD"]
seq = defaultdict(list)
want = re.compile("|".join(re.escape(p) for p in PATTERNS))
with GT.open(newline="", errors="replace") as fh:
    for i, row in enumerate(csv.DictReader(fh), start=2):
        nid = row["nodeid"]
        if want.search(nid):
            seq[nid].append((i, row["date"], row["value"], row.get("dtype", "")))


def parse_ts(ts):
    # 2020-07-20 08:55:23.968000
    from datetime import datetime
    try:
        return datetime.strptime(ts[:26], "%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        try:
            return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def classify(values, dts, dtypes):
    vals = [v for _, _, v, _ in values]
    numeric = []
    for v in vals:
        try:
            numeric.append(float(v))
        except Exception:
            numeric.append(None)
    distinct = len(set(vals))
    boolish = set(vals) <= {"True", "False", "0", "1"}
    is_num = all(x is not None for x in numeric)
    increasing = is_num and all(b >= a for a, b in zip(numeric, numeric[1:]))
    drops = sum(1 for a, b in zip(numeric, numeric[1:]) if b < a) if is_num else None
    dt_med = statistics.median([d.total_seconds() for d in dts if d]) if dts else None
    dt_range = (min(d.total_seconds() for d in dts), max(d.total_seconds() for d in dts)) if dts else (None, None)
    cls = "UNKNOWN"
    if boolish and distinct <= 2:
        cls = "BOOLEAN_FLAG"
    elif is_num and increasing and drops == 0 and distinct > 3:
        cls = "MONOTONIC_COUNTER_OR_TIMER"
    elif is_num and distinct > 3 and drops and drops > 0 and dt_med is not None:
        cls = "SAWTOOTH_COUNTER_OR_TIMER"
    elif is_num and distinct > 3:
        cls = "NUMERIC_MEASUREMENT"
    return {"distinct": distinct, "dtype": dtypes[0] if dtypes else "", "class": cls,
            "monotonic": increasing if is_num else None, "drops": drops,
            "dt_median_s": round(dt_med, 6) if dt_med is not None else None,
            "dt_min_s": round(dt_range[0], 6) if dt_range[0] is not None else None,
            "dt_max_s": round(dt_range[1], 6) if dt_range[1] is not None else None,
            "v_min": min(numeric) if is_num and numeric else None,
            "v_max": max(numeric) if is_num and numeric else None}


rows, detail = [], {}
for nid, entries in sorted(seq.items(), key=lambda kv: -len(kv[1])):
    dts = []
    prev = None
    for _, ts, _, _ in entries:
        t = parse_ts(ts)
        if t and prev and t >= prev:
            dts.append(t - prev)
        prev = t or prev
    info = classify(entries, dts, [e[3] for e in entries])
    family = next((p for p in PATTERNS if p in nid), "other")
    rows.append({"nodeid": nid, "family": family, "transitions": len(entries) - 1, **info})
    if len(detail) < 40:
        detail[nid] = {"first_lines": [{"line": e[0], "ts": e[1], "value": e[2]} for e in entries[:8]],
                       "last_lines": [{"line": e[0], "ts": e[1], "value": e[2]} for e in entries[-3:]]}
with (OUT / "plc_signal_semantics_audit.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
(OUT / "plc_signal_sequences_sample.json").write_text(json.dumps(detail, indent=1))
clock = [{"nodeid": r["nodeid"], "transitions": r["transitions"],
          "dt_median_s": r["dt_median_s"], "distinct": r["distinct"]}
         for r in rows if r["family"] == "Taktmerker"]
with (OUT / "clock_signal_detection.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["nodeid", "transitions", "dt_median_s", "distinct"])
    w.writeheader(); w.writerows(clock)
print("audited nodes:", len(rows))
from collections import Counter
print("classes:", dict(Counter(r["class"] for r in rows)))
print("families:", dict(Counter(r["family"] for r in rows)))
