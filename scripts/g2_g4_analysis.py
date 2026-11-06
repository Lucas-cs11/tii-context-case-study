#!/usr/bin/env python3
"""G2-G4 evidence extraction from the CONTEXT OPC-UA logs.

Outputs
  signal_classification.csv   node -> class/unit (data-type driven, not name-only)
  tu_pair_diff_stats.csv      paired .T/.U difference statistics
  activity_windows.csv        boolean step-active windows with line numbers
  cycle_summary.csv           per-node cycle counts and dwell durations
  concurrency_overlaps.csv    cross-station overlap of activity windows
  pressure_summary.csv        pressure signals per scenario
  g2_g4_summary.json
"""
from __future__ import annotations
import csv, json, re, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path("data/extracted")
OUT = Path("results"); OUT.mkdir(exist_ok=True)
SCEN = {"ground_truth": "2020-07-20-1_8_g_8_n_ground_truth",
        "shuttle_dropout": "2020-07-20-3_2_g_1_n_5_g_8_n_shuttle_drop_out",
        "missing_parts": "2020-07-20-4_8_g_3_n_1_m_1_n_2_m_1_n_missing_parts",
        "missing_pressure": "2020-07-20-7-8_g_8_n_pressure"}

SELECT = re.compile(r"(\.X$|\.SM$|\.S[01]$|Ist-Druck|Soll-Druck|SQ_BUSY|SA_BUSY|"
                    r"Zustandsautomat|Ablaufsteuerung_iDB|Ablaufkette_iDB\.Init|"
                    r"AblaufketteShuttle_DB\.Init|Taktmerker|Shuttletueren|"
                    r"Programm wird ausgefuehrt|M1 |M2 )")


def ts(s):
    for fmt, n in (("%Y-%m-%d %H:%M:%S.%f", 26), ("%Y-%m-%d %H:%M:%S", 19)):
        try:
            return datetime.strptime(s[:n], fmt)
        except Exception:
            continue
    return None


def q(v, p):
    v = sorted(v); k = (len(v) - 1) * p; lo = int(k); hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def classify(nodeid, values, dtypes):
    dt = (dtypes[0] if dtypes else "").lower()
    name = nodeid.split(".")[-1]
    low = nodeid.lower()
    dist = set(values)
    if dist <= {"True", "False"}:
        if ".x" in nodeid.lower() and ("ablauf" in low or "programm" in low or "tueren" in low):
            return "STEP_ACTIVE_FLAG", ""
        return "BOOLEAN_FLAG", ""
    numeric = []
    for v in values:
        try:
            numeric.append(float(v))
        except Exception:
            numeric = None; break
    if not numeric:
        return "NON_NUMERIC", ""
    unit = ""
    if "[bar]" in low:
        unit = "bar"
    elif "[%]" in low or "ist-druck" in low:
        unit = "%"
    mono = all(b >= a for a, b in zip(numeric, numeric[1:]))
    if name in ("T", "U"):
        return "STEP_TIMER", "ms"
    if unit:
        return "ANALOG_PROCESS_VALUE", unit
    if mono and len(set(numeric)) > 3:
        return "MONOTONIC_COUNTER", ""
    if "taktmerker" in low:
        return "PLC_CLOCK", ""
    return "NUMERIC_OTHER", ""


def main() -> int:
    windows_all, cls_all, tu_stats, pressure, cycle_rows = [], [], [], [], []
    overlaps, summary = [], {}
    for label, d in SCEN.items():
        path = ROOT / d / "data_opcua.csv"
        seq = defaultdict(list)
        with path.open(newline="", errors="replace") as fh:
            for i, row in enumerate(csv.DictReader(fh), start=2):
                if SELECT.search(row["nodeid"]):
                    seq[row["nodeid"]].append((i, row["date"], row["value"], row.get("dtype", "")))
        summary[label] = {"selected_nodes": len(seq),
                          "selected_rows": sum(len(v) for v in seq.values())}
        # classification
        for nid, entries in seq.items():
            vals = [e[2] for e in entries]
            c, unit = classify(nid, vals, [e[3] for e in entries])
            cls_all.append({"scenario": label, "nodeid": nid, "class": c, "unit": unit,
                            "transitions": len(entries) - 1, "distinct": len(set(vals))})
        # .T/.U pairs
        by_suffix = {}
        for nid, entries in seq.items():
            for suf in (".T", ".U"):
                if nid.endswith(suf):
                    by_suffix.setdefault(nid[:-2], {})[suf] = entries
        for base, pair in by_suffix.items():
            if ".T" not in pair or ".U" not in pair:
                continue
            t_vals = [e[2] for e in pair[".T"]]
            u_vals = [e[2] for e in pair[".U"]]
            n = min(len(t_vals), len(u_vals))
            diffs = []
            for a, b in zip(t_vals[:n], u_vals[:n]):
                try:
                    diffs.append(float(a) - float(b))
                except Exception:
                    pass
            if not diffs:
                continue
            nz = [x for x in diffs if x != 0]
            tu_stats.append({"scenario": label, "pair": base, "paired_samples": len(diffs),
                             "equal_ratio": round(sum(1 for x in diffs if x == 0) / len(diffs), 4),
                             "diff_min": min(diffs), "diff_max": max(diffs),
                             "diff_median": statistics.median(diffs),
                             "u_gt_t_count": sum(1 for x in diffs if x < 0),
                             "nonzero_count": len(nz)})
        # activity windows for step-active flags
        for nid, entries in seq.items():
            if not nid.endswith(".X"):
                continue
            prev = None
            start = None
            for line, tss, val, _ in entries:
                t = ts(tss)
                if prev is None:
                    if val == "True":
                        start = {"line": line, "ts": tss, "t": t, "open_at_start": True}
                    prev = val
                    continue
                if val != prev:
                    if val == "True":
                        start = {"line": line, "ts": tss, "t": t, "open_at_start": False}
                    elif start is not None:
                        windows_all.append({"scenario": label, "nodeid": nid,
                                            "start": start["ts"], "end": tss,
                                            "duration_s": (t - start["t"]).total_seconds() if start["t"] and t else None,
                                            "start_line": start["line"], "end_line": line,
                                            "open_at_start": start["open_at_start"],
                                            "open_at_end": False})
                        start = None
                    prev = val
            if start is not None:
                windows_all.append({"scenario": label, "nodeid": nid, "start": start["ts"],
                                    "end": None, "duration_s": None,
                                    "start_line": start["line"], "end_line": None,
                                    "open_at_start": start["open_at_start"], "open_at_end": True})
        # cycles per .X node
        for nid in [n for n in seq if n.endswith(".X")]:
            ws = [w for w in windows_all if w["scenario"] == label and w["nodeid"] == nid]
            closed = [w for w in ws if w["duration_s"] is not None]
            if closed:
                durs = [w["duration_s"] for w in closed]
                cycle_rows.append({"scenario": label, "nodeid": nid, "activations": len(ws),
                                   "closed_windows": len(closed),
                                   "open_at_start": sum(1 for w in ws if w["open_at_start"]),
                                   "open_at_end": sum(1 for w in ws if w["open_at_end"]),
                                   "dur_median_s": round(statistics.median(durs), 4),
                                   "dur_min_s": round(min(durs), 4),
                                   "dur_max_s": round(max(durs), 4),
                                   "dur_p5_s": round(q(durs, 0.05), 4),
                                   "dur_p95_s": round(q(durs, 0.95), 4)})
        # pressure signals
        for nid, entries in seq.items():
            if "Ist-Druck" in nid or "Soll-Druck" in nid:
                vals = []
                for _, _, v, _ in entries:
                    try:
                        vals.append(float(v))
                    except Exception:
                        pass
                if vals:
                    pressure.append({"scenario": label, "nodeid": nid, "samples": len(vals),
                                     "min": round(min(vals), 4), "median": round(statistics.median(vals), 4),
                                     "max": round(max(vals), 4), "distinct": len(set(vals))})
    # cross-station overlaps inside each scenario (station-level activity windows)
    for label in SCEN:
        ws = [w for w in windows_all if w["scenario"] == label and w["duration_s"] is not None]
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                a, b = ws[i], ws[j]
                sa = a["nodeid"].split("Station")[-1][:3] if "Station" in a["nodeid"] else a["nodeid"][:12]
                sb = b["nodeid"].split("Station")[-1][:3] if "Station" in b["nodeid"] else b["nodeid"][:12]
                if sa == sb:
                    continue
                ta0, ta1 = ts(a["start"]), ts(a["end"])
                tb0, tb1 = ts(b["start"]), ts(b["end"])
                if not all([ta0, ta1, tb0, tb1]):
                    continue
                ov = (min(ta1, tb1) - max(ta0, tb0)).total_seconds()
                if ov > 0:
                    overlaps.append({"scenario": label, "station_a": sa, "node_a": a["nodeid"][-60:],
                                     "station_b": sb, "node_b": b["nodeid"][-60:],
                                     "overlap_s": round(ov, 3),
                                     "start_a": a["start"], "end_a": a["end"],
                                     "start_b": b["start"], "end_b": b["end"]})
    def dump(name, rows):
        if rows:
            with (OUT / name).open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)
    dump("signal_classification.csv", cls_all)
    dump("tu_pair_diff_stats.csv", tu_stats)
    dump("activity_windows.csv", windows_all)
    dump("cycle_summary.csv", cycle_rows)
    dump("concurrency_overlaps.csv", overlaps[:2000])
    dump("pressure_summary.csv", pressure)
    (OUT / "g2_g4_summary.json").write_text(json.dumps(
        {"scenarios": summary, "windows": len(windows_all), "closed_windows":
         sum(1 for w in windows_all if w["duration_s"] is not None),
         "overlaps": len(overlaps), "pressure_signals": len(pressure)}, indent=1))
    print(json.dumps({"scenarios": summary, "windows": len(windows_all),
                      "overlaps": len(overlaps)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
