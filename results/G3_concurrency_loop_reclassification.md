# G3 concurrency and loop evidence (reclassified)

## Concurrency classes

| Class | Status | Evidence |
|---|---|---|
| `OBSERVED_CONTROLLER_STATE_OVERLAP` | **established** | Press `Step3.X` and robot program windows overlap in 43 pairs (max overlap 31.5 s); press Step3 overlaps the St60 shuttle chain in 43 pairs (max 199.2 s) |
| `OBSERVED_STATION_CONCURRENCY` | **established** | the overlapping windows belong to different station controllers (Station 60 press vs Station 50 robot) and exceed timestamp resolution |
| `OBSERVED_TWO_SHUTTLE_CONCURRENCY` | **NOT_ESTABLISHED** | no shuttle identifier, position or task id in the archive |
| `MODEL_REACHABLE_CONCURRENCY` | not applicable yet (no model) | |

`Press Step8 × robot program` overlaps in 14 pairs; `Step8 × Relais montieren` and
`Step8 × Schutzmodul montieren` have **0** overlaps, which is consistent with the press being
downstream of assembly rather than concurrent with it.

## Loops

- Production loops between parts: relay mount 15×, protection mount 15×, robot program 31×,
  press Step3 16×, press Step8 16× within 34 minutes - real repeated execution, not timer
  refresh (all are step-active flags, `.T/.U` excluded).
- **Task-internal loop before the first completion of one task: NOT_ESTABLISHED.** With no
  product identity there is no way to attribute two executions to the same workpiece.
- Shuttle dropout scenario: robot program 32 windows, press Step3 16 windows, shuttle chain
  activity differs from ground truth, but the four scenarios are independent runs, so no
  paired causal comparison is possible.
