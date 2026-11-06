# G2–G4 evidence report (CONTEXT dataset, ground-truth and fault scenarios)

Sources: GitHub Actions runs of this repository (all analysis on GitHub-hosted runners;
raw data verified in G1 with MD5 `ca10ec210b91159811f72959a868bade`). Every number below is
reproducible from `results/*.csv`.

## P0 corrections completed

1. **`.T`/`.U` are step-activation timers, not counters.** Across the 320 pairs in the
   archive they are equal in 99.55–100 % of aligned samples; where they differ, the
   difference is −2 ms or −3 ms and `U < T` (fault-interference exclusion), never more.
   The values are monotone milliseconds of step-active time with resets at step changes.
2. **`Taktmerker` is the S7 clock-memory byte** (113 values cycling 1…255, 758 downward
   steps) and is not a production counter.
3. **Signal classification is now data-type driven** (`results/signal_classification.csv`):
   1,592 `STEP_ACTIVE_FLAG`, 640 `STEP_TIMER`, 12 `PLC_CLOCK`, 12,424 boolean flags,
   40 analog process values, 2,640 other numeric.
4. **Pressure signals are percentages / raw module counts, not bars**: `M1/M2 Ventil
   Ist-Druck` (integer 464…13511), `Ventil Soll-Druck` (0…27648, Siemens 0–100 % raw),
   and a `[%]` variant 1.68…48.76. No bar calibration is present in the archive.

## G2 — recovered production activity

From 4,338 selected nodes per scenario, 3,969 discrete step-active windows were recovered
(3,885 closed), each with start/end timestamps and source line numbers
(`results/activity_windows.csv`).

Ground-truth scenario, windows per activity:

| Activity | windows | median duration | max |
|---|---:|---:|---:|
| Press step 3 (`Presse.Ablaufkette iDB.Step3.X`) | 16 | 108.5 s | 206.7 s |
| Robot program (`Roboter: Programm wird ausgefuehrt.X`) | 32 | 14.1 s | 31.5 s |
| Shuttle send (`…SendShuttleOn.X`) | 90 | 1.8 s | 22.7 s |
| Shuttle chain at St30 | 31 | 6.5 s | 203.5 s |
| Shuttle chain at St40 | 60 | 34.8 s | 107.9 s |
| Shuttle chain at St50 | 45 | 31.7 s | 167.8 s |
| Shuttle chain at St60 | 50 | 4.8 s | 199.4 s |
| Switch (`Ablaufkette_Weiche_DB`) | 55 | 3.2 s | 1182 s |

## G3 — concurrency and cycles

**Station-level concurrency is directly observed** (ground truth, closed windows only):

| Pair | overlapping pairs | max overlap |
|---|---:|---:|
| Press step 3 × Robot program | 43 | 31.5 s |
| Press step 3 × Shuttle chain St60 | 43 | 199.2 s |
| Robot program × Shuttle chain St60 | 60 | 31.5 s |
| Shuttle St40 × Shuttle St50 | 103 | 104.3 s |

Classification: `OBSERVED_STATION_CONCURRENCY` — two different station controllers are
provably active at the same time (overlaps far exceed timestamp resolution). It is **not**
`OBSERVED_TWO_SHUTTLE_CONCURRENCY`: no field in the archive carries a shuttle identifier,
so the two physical shuttles cannot be separated from the logs.

**Cycles**: 409 step flags repeat within a scenario (e.g. press step 3 activates 16 times,
robot program 32 times in 34 minutes). These are genuine production loops between
workpieces. **No task-internal loop before a single task's first completion can be
established**, because a "task" cannot be tied to one workpiece without identity.

## G4 — timing

Durations of the recovered windows are reported as `MEASURED_ACTIVITY_DURATION`
(`results/cycle_summary.csv`, per node: n, median, P5, P95, min, max, open-at-start/end
counts). They are **not** firing intervals: the archive does not expose the TPN
enable-to-fire semantics, so no `CALIBRATED_FIRING_INTERVAL` is claimed.

Pressure comparison (medians of the raw signals):

| Signal | GT | missing pressure |
|---|---:|---:|
| M1 Ist-Druck (raw) | 600 | 579 |
| M1 Soll-Druck (setpoint) | 13,423 | 12,736 |
| M2 Ist-Druck (raw) | 3,767 | 4,747 |

A pressure difference is present in the scenario, but it is **not** established as the
cause of a timing change: the scenario is a separate acquisition run, and the press step
duration (16 windows in GT vs 16 in the pressure run) does not show a clean separation
without controlling for the other concurrent activities.

**`ADJUSTMENT_NOT_ESTABLISHED`**: no PLC parameter list, engineering range or safety limit
for the valve setpoints is distributed with the data, so the firing-interval adjustment
cannot be authorised from this archive.

## G5 decision

| Gate | Verdict |
|---|---|
| G1 | PASS WITH LIMITATIONS (CC BY-NC 4.0; size corrected) |
| G2 | PASS WITH LIMITATIONS (activities recovered; no product identity) |
| G3 | PASS WITH LIMITATIONS (`OBSERVED_STATION_CONCURRENCY`; two-shuttle identity NOT_ESTABLISHED; loops between parts only) |
| G4 | PASS WITH LIMITATIONS (durations measured; no calibrated firing intervals; adjustment not established) |
| G5 | `GO_FOR_VERIFICATION_ONLY` — the data support an anonymous finite-run verification case (M2-style), not an adjustment case and not M1 |

Recommended framing: **M2 (finite production run)** with an anonymous workpiece and a task
completion defined by the observed end of the press/robot cycle. M1 (a specific relay) is
`NO_GO` because no product identifier exists. A TPN calibrated to these windows may be used
to demonstrate bounded verification on real-derived timing, but the paper must state that
the measured windows are activity durations, not calibrated firing intervals, and that the
two-shuttle separation is model-level only.
