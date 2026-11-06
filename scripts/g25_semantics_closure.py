#!/usr/bin/env python3
"""G2.5 re-audit: T/U pairing, window censoring, Step3/Step8, cycle reconstruction.

Fixes three defects of the previous pass:
  * T/U statistics were computed by index alignment; this re-pairs by timestamp and
    also reports the index-aligned result so the difference is visible.
  * activity windows did not distinguish left/right censoring.
  * press Step3 long/short alternation was not examined.
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
KEYS = ["Ablaufkette", "Relais montieren", "Schutzmodul montieren",
        "Programm wird ausgefuehrt", "Step3.X", "Step8.X", "Step1.X", "Step2.X",
        "Pruefung mit DC", "Pruefung ohne DC"]


def ts(s):
    for f, n in (("%Y-%m-%d %H:%M:%S.%f", 26), ("%Y-%m-%d %H:%M:%S", 19)):
        try:
            return datetime.strptime(s[:n], f)
        except Exception:
            pass
    return None


def q(v, p):
    v = sorted(v); k = (len(v) - 1) * p; lo = int(k); hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def main() -> int:
    tu_rows, tu_global = [], []
    win_rows, seq_rows = [], []
    conc_rows = []
    global_pairs = global_equal = global_nonzero = 0
    global_diffs = []
    for label, d in SCEN.items():
        seq = defaultdict(list)
        with (ROOT / d / "data_opcua.csv").open(newline="", errors="replace") as fh:
            for i, row in enumerate(csv.DictReader(fh), start=2):
                nid = row["nodeid"]
                if any(k in nid for k in KEYS):
                    seq[nid].append((i, row["date"], row["value"], row.get("dtype", "")))
        # ---------- P0-A: T/U pairing by timestamp ----------
        for nid in list(seq):
            if not nid.endswith(".T"):
                continue
            u_nid = nid[:-2] + ".U"
            if u_nid not in seq:
                continue
            t_map = {}
            for line, tss, val, _ in seq[nid]:
                t_map.setdefault(tss, float(val))
            u_map = {}
            for line, tss, val, _ in seq[u_nid]:
                u_map.setdefault(tss, float(val))
            common = sorted(set(t_map) & set(u_map))
            diffs = [t_map[t] - u_map[t] for t in common]
            # index alignment (old method) for comparison
            t_vals = [float(e[2]) for e in seq[nid]]
            u_vals = [float(e[2]) for e in seq[u_nid]]
            n = min(len(t_vals), len(u_vals))
            idx_diffs = [t_vals[k] - u_vals[k] for k in range(n)]
            def stat(vals):
                if not vals:
                    return {}
                return {"samples": len(vals),
                        "equal_ratio": round(sum(1 for x in vals if x == 0) / len(vals), 6),
                        "nonzero": sum(1 for x in vals if x != 0),
                        "u_gt_t": sum(1 for x in vals if x < 0),
                        "t_gt_u": sum(1 for x in vals if x > 0),
                        "min": min(vals), "max": max(vals), "median": statistics.median(vals)}
            s_ts, s_idx = stat(diffs), stat(idx_diffs)
            tu_rows.append({"scenario": label, "pair": nid[:-2],
                            "ts_samples": s_ts.get("samples"), "ts_equal": s_ts.get("equal_ratio"),
                            "ts_nonzero": s_ts.get("nonzero"), "ts_u_gt_t": s_ts.get("u_gt_t"),
                            "ts_t_gt_u": s_ts.get("t_gt_u"), "ts_min": s_ts.get("min"),
                            "ts_max": s_ts.get("max"),
                            "idx_samples": s_idx.get("samples"), "idx_equal": s_idx.get("equal_ratio"),
                            "idx_nonzero": s_idx.get("nonzero")})
            global_pairs += len(diffs)
            global_equal += sum(1 for x in diffs if x == 0)
            global_nonzero += sum(1 for x in diffs if x != 0)
            global_diffs += diffs
        # ---------- P0-B: windows with censoring ----------
        for nid, entries in seq.items():
            if not nid.endswith(".X"):
                continue
            first_true_at_start = entries[0][2] == "True"
            start = None
            for line, tss, val, _ in entries:
                t = ts(tss)
                if start is None:
                    if val == "True":
                        start = {"line": line, "ts": tss, "t": t,
                                 "left_censored": first_true_at_start and line == entries[0][0]}
                    continue
                if val == "False":
                    right_censored = line == entries[-1][0]
                    censor = ("BOTH_CENSORED" if start["left_censored"] and right_censored
                              else "LEFT_CENSORED" if start["left_censored"]
                              else "RIGHT_CENSORED" if right_censored
                              else "FULLY_OBSERVED")
                    win_rows.append({"scenario": label, "nodeid": nid,
                                     "start": start["ts"], "end": tss,
                                     "duration_s": round((t - start["t"]).total_seconds(), 4) if start["t"] and t else None,
                                     "start_line": start["line"], "end_line": line,
                                     "censoring": censor})
                    start = None
            if start is not None:
                win_rows.append({"scenario": label, "nodeid": nid, "start": start["ts"],
                                 "end": None, "duration_s": None,
                                 "start_line": start["line"], "end_line": None,
                                 "censoring": "LEFT_CENSORED" if start["left_censored"] else "RIGHT_CENSORED"})
        # ---------- P0-C: press step sequence ----------
        for nid in seq:
            if "Presse" in nid and re.search(r"Step(3|8)\.X$", nid):
                wins = [w for w in win_rows if w["scenario"] == label and w["nodeid"] == nid]
                for w in wins:
                    seq_rows.append({"scenario": label, "nodeid": nid, "start": w["start"],
                                     "end": w["end"], "duration_s": w["duration_s"],
                                     "censoring": w["censoring"]})
    # aggregate T/U
    if global_diffs:
        def st(vals):
            return {"samples": len(vals), "equal": sum(1 for x in vals if x == 0),
                    "equal_ratio": round(sum(1 for x in vals if x == 0) / len(vals), 6),
                    "nonzero": sum(1 for x in vals if x != 0),
                    "nonzero_pairs": sum(1 for r in tu_rows if int(r.get("ts_nonzero") or 0) > 0),
                    "u_gt_t": sum(1 for x in vals if x < 0), "t_gt_u": sum(1 for x in vals if x > 0),
                    "min": min(vals), "max": max(vals), "median": statistics.median(vals),
                    "p5": q(vals, 0.05), "p95": q(vals, 0.95)}
        tu_global.append(st(global_diffs))
    # window duration stats by censoring class
    agg = {}
    for w in win_rows:
        c = w["censoring"]
        agg.setdefault(c, []).append(w)
    summary = {"windows": len(win_rows),
               "by_censoring": {k: len(v) for k, v in agg.items()},
               "tu_global": tu_global, "tu_rows": len(tu_rows)}
    # fully-observed durations for the named activities
    named = defaultdict(list)
    for w in win_rows:
        if w["censoring"] != "FULLY_OBSERVED" or w["duration_s"] is None:
            continue
        for k in KEYS:
            if k in w["nodeid"]:
                named[(w["scenario"], k)].append(w["duration_s"])
                break
    summary["named_fully_observed"] = {
        f"{s}|{k}": {"n": len(v), "median": round(statistics.median(v), 3),
                     "min": round(min(v), 3), "max": round(max(v), 3),
                     "p5": round(q(v, .05), 3), "p95": round(q(v, .95), 3)}
        for (s, k), v in sorted(named.items())}
    def dump(name, rows):
        if rows:
            with (OUT / name).open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)
    dump("tu_pair_diff_stats_v2.csv", tu_rows)
    dump("tu_global_stats.csv", tu_global)
    dump("activity_windows_v2.csv", win_rows)
    dump("press_step_sequence.csv", seq_rows)
    (OUT / "g25_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({"windows": len(win_rows), "by_censoring": summary["by_censoring"],
                      "tu_global": tu_global, "tu_pairs": len(tu_rows)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
