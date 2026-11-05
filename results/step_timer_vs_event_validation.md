# P0 — step timers versus production events

## What `.T` and `.U` actually are (empirical)

| Node pair | transitions T / U | value range T | value range U | identical |
|---|---|---|---|---|
| `Init.T` / `.U` | 8455 / 8455 | 5025680.0..7100496.0 | 5025680.0..7100496.0 | True |
| `Init.T` / `.U` | 8408 / 8408 | 9.0..109821.0 | 9.0..109821.0 | True |
| `Step127.T` / `.U` | 661 / 661 | 4990632.0..7063213.0 | 4990632.0..7063213.0 | True |
| `Shuttletueren oeffen (Auto).T` / `.U` | 437 / 437 | 55.0..601251.0 | 55.0..601251.0 | True |
| `Roboter: Programm wird ausgefuehrt.T` / `.U` | 219 / 219 | 19.0..11383.0 | 19.0..11383.0 | True |

Every `.T`/`.U` pair in the archive carries **the same value sequence**, the same
transition count and the same range, and the values are **monotonically increasing at
roughly constant inter-arrival time** (0.23 s for Station 20, 3.1 s for the robot) with
occasional resets when the step changes.

This is the S7-GRAPH step-activation time pair: `.T` is the step activation time and
`.U` the activation time excluding fault interference; both count in milliseconds of
step-active time. `Ablaufkette_iDB.Init.T` grows from 5,025,680 to 7,100,496 ms, i.e. about
2.1e6 ms of accumulated step time over a 34-minute recording - consistent with a timer that
keeps running while a step is active, **not** with a counter of parts.

**Consequence: the transition counts of `.T`/`.U` (8,455 for Station 20) are timer update
samples, not operation counts. They must not be used as event counts or as cycle counts.**

## `Taktmerker` is a clock-memory byte

113 distinct values cycling 1...255 with 758 downward steps and a 1.8 s median update -
the S7 clock-memory byte (bits at 0.5-10 Hz), not a production counter. It can serve as a
coarse timebase check only.

## Signals that do carry process meaning

| NodeId | Behaviour | Usable as |
|---|---|---|
| `...SQ_FLAGS.SQ_BUSY` (19 active nodes) | boolean, dwell ~0.3 s | occupancy window of a sequence/transport unit (needs cycle-boundary validation) |
| `...M1 Ventil Ist-Druck [%]` | float 1.68...48.76, and a raw variant 464...13511 | **percentage** signal of the press valve, not absolute pressure |
| `...Shuttletueren oeffen (Auto).T/U` | step timer | step duration, not a count |
| `...Roboter: Programm wird ausgefuehrt.T/U` | step timer | robot program execution duration |

## Correction to the earlier G2 report

The earlier statement "Ablaufkette counters bound the process phases and 8,408 transitions
are 8,408 operations" is **withdrawn**. Only the *resets* of these timers mark step changes,
and step changes must be recovered from the sequence-DB step state, not from timer updates.
