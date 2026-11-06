# G2.5 anonymous production-cycle reconstruction

All numbers use FULLY_OBSERVED windows only (`results/activity_windows_v2.csv`).

## Named activities in the ground-truth scenario

| Activity | windows | median | P5 | P95 | min | max |
|---|---:|---:|---:|---:|---:|---:|
| `Relais montieren.X` | 15 | 9.38 s | 9.28 | 12.57 | 9.25 | 12.64 |
| `Schutzmodul montieren.X` | 15 | 12.48 s | 9.45 | 12.55 | 9.29 | 12.59 |
| `Roboter: Programm wird ausgefuehrt.X` | 31 | 18.74 s | 6.24 | 31.30 | 6.20 | 31.45 |
| `Presse … Step8.X` | 16 | see `press_step_sequence.csv` | | | | |
| `Pruefung mit DC (Auto).X` | 12 | see activity table | | | | |
| `Pruefung ohne DC (Auto).X` | 3 | see activity table | | | | |

## What the pairing shows

For each robot-program window we counted how many relay-mount and protection-module windows
fall completely inside it:

| (relay, protection) inside one robot window | robot windows |
|---|---:|
| (1, 1) | 12 |
| (1, 0) | 1 |
| (0, 1) | 1 |
| (0, 0) | 17 |

Robot program durations alternate between ~31 s and ~6 s; the 31 s windows are exactly the
ones containing one relay mount plus one protection mount. **12 complete anonymous assembly
units** can therefore be reconstructed, and 15 relay + 15 protection windows exist in total.

## What cannot be concluded

- No product identity exists, so a unit cannot be followed across the press and inspection
  stations; the assembly unit and the press cycle can only be matched by time containment,
  not by identity.
- The press Step3 windows (16) do not alternate in step with the 12 assembly units, and
  Step3 includes long/short modes (P0-C), so "16 press cycles" of 16 different parts is not
  established.
- There is no recorded run-completion event; the end of the recording is not a task
  completion.
