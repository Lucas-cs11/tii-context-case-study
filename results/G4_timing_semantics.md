# G4 timing semantics

- Measured activity durations are reported as `MEASURED_ACTIVITY_DURATION` per node with
  n / median / P5 / P95 / min / max over FULLY_OBSERVED windows only.
- **No `CALIBRATED_FIRING_INTERVAL` is claimed.** To calibrate a firing interval one must
  show that the TPN transition is enabled exactly when the PLC step is active and that
  firing happens at the step exit. The logs show step-active windows, but:
  1. the press Step3 alternates long/short modes, so the step contains waiting phases;
  2. the relay/protection steps overlap with robot motion rather than being isolated;
  3. the archive has no PLC symbol documentation to prove the enable/fire mapping.
- **`ADJUSTMENT_NOT_ESTABLISHED`**: no PLC parameter list, engineering range or safety limit
  is distributed with the data; the valve setpoints (`Soll-Druck`, raw 0-27648) cannot be
  converted into an authorised adjustment range.
- Pressure: the pressure scenario shows different medians (M1 raw 600 vs 579, M2 raw 3767 vs
  4747) but press Step3 durations are almost identical to ground truth
  (146.3/47.2/180.8/51.0 ... vs 161.7/37.8/190.4/50.4 ...), so no pressure-to-timing causal
  claim is supported.
