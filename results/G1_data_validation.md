# G1 — data authenticity and integrity

## Source

| Item | Value |
|---|---|
| Repository | https://zenodo.org/records/4034867 |
| DOI | 10.5281/zenodo.4034867 |
| File | `kaupp_context_dataset.zip` (v2) |
| MD5 (official and verified) | `ca10ec210b91159811f72959a868bade` |
| Size | 23,418,302 bytes |
| Download | GitHub Actions run `42044605897` (first attempt), `42044887269` (successful extraction) |
| Archive integrity | zip member list readable; extraction required 7z because the archive uses a compression method Python's `zipfile` cannot decompress |
| Members | 29 (4 scenario directories, 24 CSV files, 5 further files) |

The download is executed by `scripts/download_context.py` inside the GitHub Actions workflow
`.github/workflows/download.yml`; it retries five times over two Zenodo URLs, verifies the
MD5 before extraction, and never modifies the archive contents.

## Scenarios present in v2

| Directory | OPC-UA rows | Observed interval (UTC) | Duration |
|---|---:|---|---:|
| `2020-07-20-1_8_g_8_n_ground_truth` | 390,562 | 08:55:23.968 – 09:29:59.110 | 34.6 min |
| `2020-07-20-3_2_g_1_n_5_g_8_n_shuttle_drop_out` | 454,589 | 11:33:57.410 – 12:15:37.258 | 41.7 min |
| `2020-07-20-4_8_g_3_n_1_m_1_n_2_m_1_n_missing_parts` | 377,846 | 13:14:47.901 – 13:49:01.206 | 34.2 min |
| `2020-07-20-7-8_g_8_n_pressure` | 388,890 | 18:08:22.612 – 18:43:03.242 | 34.7 min |

Each scenario also contains five equipment logs (storage, shuttle, robot, press, inspection),
17.4k–22.5k rows each. The four scenarios are **independent acquisition runs**; they are not
a single continuous execution and are therefore never concatenated into one trace.

## OPC-UA structure

`data_opcua.csv` columns: `date, nodeid, value, dtype` (one row per asynchronous value change,
no explicit old/new pair — the previous value must be reconstructed per node).

| Scenario | distinct NodeIds | Station 10 | Station 20 | Station 30 | Station 40 | Station 50 | Station 60 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ground truth | 33,056 | 8,829 | 3,315 | 3,979 | 7,900 | 6,051 | 2,982 |

The same NodeId set (33,056) appears in all four scenarios, which is expected because the same
PLC program is logged. NodeIds are hierarchical, e.g.
`ns=6;s=Station 20 OpenC.St20 SoftSPS.AblaufketteShuttle_DB.Init.T` or
`ns=6;s=S71500ET200MP-Station_1.Station 60 - Presse.Taktmerker Byte`.
No station name is invented; all station attributions above come from the NodeId strings.

## Status of G1

- MD5 verified: **PASS**
- archive integrity and member listing: **PASS**
- file list, row counts, time ranges: **PASS**
- CSV header / missing-value inventory: **PASS** (`results/csv_inventory.json`)
- independent scenario separation confirmed: **PASS**
- licence metadata: **PENDING** — the Zenodo record metadata has not yet been captured in the
  pipeline; it must be recorded before redistribution of any raw file in the final package.
