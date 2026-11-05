# Corrections to the first G2 report

| Earlier statement | Status | Evidence |
|---|---|---|
| `Ablaufkette*.Init.T/U` are sequence counters whose change count is the number of operations | **WRONG — withdrawn** | T and U are identical monotone millisecond step timers; 8,455 updates are timer samples |
| `AblaufketteShuttle_DB` (Station 20) and `Presse.Ablaufkette` (Station 60) are two independent shuttles | **UNSUPPORTED — withdrawn** | both are step timers of different stations; no shuttle identity is encoded |
| `Taktmerker Byte` counts production cycles | **WRONG — withdrawn** | 113 values cycling 1..255 = S7 clock-memory byte |
| `M1 Ventil Ist-Druck [%]` gives the absolute pressure | **CORRECTED** | it is a percentage (1.68..48.76 %); a separate raw variant (464..13511) exists; no calibration to bar is available |
| `SQ_BUSY` indicates shuttle occupancy | **OPEN** | boolean flags exist (19 active), dwell ~0.3 s; cycle-level meaning must be validated before use |
| Equipment CSVs are event logs | **WRONG — withdrawn** | they are sensor logs (light, pressure, temperature, IMU); `TCAp` and `sGRP` are constant 0 |
| Product identity is recoverable | **NOT ESTABLISHED** | no RFID/DMC/order identifier found in the 33,056 NodeIds nor in the sensor logs |
