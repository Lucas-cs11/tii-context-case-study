# G2 — production event recovery (status report)

Run `42051441545` (commit at time of run), data verified in G1.

## What the logs actually contain

1. `data_opcua.csv` per scenario: 377k–454k rows of asynchronous PLC value changes
   (`date, nodeid, value, dtype`), 33,056 distinct NodeIds, of which
   **2,694–2,710 actually change state** during the recorded window. The remaining
   ~30,350 NodeIds are static configuration/system variables and are not events.
2. The five "equipment logs" per scenario are **sensor loggers, not event logs**:
   columns are `datetime, TCAp, sGRP, TSL_IR, TSL_Full, TSL_Vis, TSL_LUX,
   BMP_TempC, BMP_Pa, BMP_AltM, MPU_Accel*, MPU_Gyro*, MPU_Mag*`, with `TCAp` and
   `sGRP` constant zero in every file inspected. They carry no product, order or
   shuttle identifier and no discrete event labels.

## Production-relevant active NodeIds (ground truth scenario)

| Station | NodeId (suffix) | Transitions | Meaning (evidence level) |
|---|---|---:|---|
| 20 | `Ablaufkette iDB.Init.T/U` | 8,454 / 8,455 | sequence-chain counter pair, continues through the whole run |
| 20 | `AblaufketteShuttle_DB.Init.T/U` | 8,408 | second sequence chain, explicitly named "Shuttle" |
| 20 | `AblaufketteShuttle_DB.RT_DATA.SQ_FLAGS.SQ_BUSY` | 1,198 | shuttle-busy flag, boolean |
| 20 | `WP321DR_DB.LIFEBIT`, `sy_CoCMD`, `sw_Lifebit_0ld`, `s_IO_DATA.COORDINATION` | 2,058 each | mirror/derived variables of the same DB - must be de-duplicated |
| 60 | `Station 60 - Presse.Ablaufkette iDB.Step3.T/U` | 1,145 | press sequence step 3 counter |
| 60 | `Station 60 - Presse.Taktmerker Byte` | 1,154 | press cycle clock byte |
| 60 | `Station 60 - Presse.M1 Ventil Ist-Druck [%]` | 1,125 | **actual valve pressure** - direct evidence for the pressure scenario |
| 60 | `Station 60 - Presse.Work IO.PIC` | 1,129 | work IO block |

These are concrete, checkable event sources: sequence-step counters bound the process
phases, `SQ_BUSY` gives shuttle occupancy, and `M1 Ventil Ist-Druck` gives the pressure
signal used by the F3 scenario.

## What is not yet recovered

- **Product / order identity**: no NodeId name contains RFID, DMC, order or pallet
  identifiers in the active set examined. The equipment CSVs cannot supply it either.
  A unique `Order -> Storage -> Robot -> Press -> Inspection` trace per product is
  therefore **not established** at this stage.
- **Station handshake semantics** (which step counter value corresponds to "part
  clamped", "press down", "part released") require the station PLC symbol tables,
  which are not part of the Zenodo archive.
- Clock nodes (0.5–10 Hz) and `DATE_TIME_SPS` are system clocks; they must be excluded
  from event counting, otherwise one physical action would be counted many times.

## Consequence for M1 / M2

M1 (first completion of a specific relay) requires product identity; it is currently
blocked by the absence of an identifier. M2 (bounded production run) is still plausible
if the sequence counters define cycles and the number of parts per run can be fixed from
the press/inspection step counts - but the part-to-part boundary must be established
from the step counters, not assumed.

## Next steps (not yet executed)

1. Reconstruct the press and shuttle step sequences from the `Ablaufkette*` counters and
   `Taktmerker Byte`; derive cycle boundaries and check whether consecutive cycles are
   genuinely alternating (loop evidence) before the first completion.
2. Correlate the two shuttle sequence chains (`AblaufketteShuttle_DB` at Station 20 and
   Station 60) to obtain two shuttle timelines and check interval overlap.
3. Extract `M1 Ventil Ist-Druck` and step counters for the pressure scenario and compare
   with ground truth to bound the pressure-induced timing change.
4. Only then decide G5 (GO / NO-GO) and M1/M2.

No TPN has been constructed yet, because the task requires G2–G4 evidence first and the
product-identity question is still open.
