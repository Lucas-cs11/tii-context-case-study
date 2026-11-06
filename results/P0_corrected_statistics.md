# P0 corrected statistics (this pass supersedes the earlier P0 claims)

## P0-A T/U pairing

Two pairing methods are now reported, because the earlier report used only the second one
and only the top rows.

| Method | samples | equal ratio | nonzero | pairs with nonzero | diff range |
|---|---:|---:|---:|---:|---|
| **timestamp pairing (canonical)** | 133,724 | **96.06 %** | 5,264 | 183 | -27.0 … 0.0 ms |
| index pairing (previous method) | see `tu_pair_diff_stats_v2.csv` column `idx_*` | — | — | — | — |

All observed deviations have `U <= T` (u_gt_t = 5264, t_gt_u = 0), i.e. the
"activation time excluding fault interference" is never larger than the raw activation
time; the largest deviation seen is 27.0 ms.

The earlier figures (".55-100 % equal, only -2/-3 ms") came from a **filtered node set and
index alignment**; they are withdrawn. The user-side count (90,851 samples / 2,957 unequal /
72 pairs / -16..+2 ms) differs because it uses a different node subset; the canonical
statistics above are computed on every `.T/.U` pair found in the log with timestamp matching,
and the per-pair table is delivered so any subset can be recomputed.

## P0-B window censoring

| Class | windows |
|---|---:|
| FULLY_OBSERVED | 3150 |
| LEFT_CENSORED | 76 |
| RIGHT_CENSORED | 401 |
| total | 3627 |

Duration statistics are computed from FULLY_OBSERVED windows only
(`results/activity_windows_v2.csv` records the class of every window).

## P0-C press Step3 is not a physical pressing duration

Ground-truth `Presse.Ablaufkette iDB.Step3.X` closed windows alternate between a long and a
short mode (161.7, 37.8, 190.4, 50.4, 185.0, 50.4, 184.9, 50.2, 184.8, 50.0, 199.2, 53.8 s ...).
The same alternation appears in the other three scenarios (shuttle-dropout: 150.8, 48.7,
181.5, 52.0, 226.4, 224.4 ... - here the alternation partly breaks down and two long phases
appear consecutively), so Step3 covers more than the press stroke and cannot be used as
"physical pressing time".
