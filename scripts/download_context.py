#!/usr/bin/env python3
"""Download the CONTEXT dataset from Zenodo, verify MD5, and inventory it."""
from __future__ import annotations
import hashlib, json, sys, time, urllib.request, zipfile
from pathlib import Path

URLS = [
    "https://zenodo.org/records/4034867/files/kaupp_context_dataset.zip?download=1",
    "https://zenodo.org/record/4034867/files/kaupp_context_dataset.zip?download=1",
]
EXPECTED_MD5 = "ca10ec210b91159811f72959a868bade"
OUT = Path("data"); OUT.mkdir(exist_ok=True)
DEST = OUT / "kaupp_context_dataset.zip"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch() -> None:
    last = None
    for attempt in range(5):
        for url in URLS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "context-case-study/1.0"})
                with urllib.request.urlopen(req, timeout=180) as r, open(DEST, "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                got = md5(DEST)
                print(f"downloaded {url} md5={got}")
                if got == EXPECTED_MD5:
                    return
                last = f"md5 mismatch: {got} != {EXPECTED_MD5}"
            except Exception as exc:  # noqa: BLE001
                last = f"{type(exc).__name__}: {exc}"
                print("attempt failed:", last)
        time.sleep(10 * (attempt + 1))
    raise SystemExit(f"download failed: {last}")


def main() -> int:
    fetch()
    assert md5(DEST) == EXPECTED_MD5
    import shutil, subprocess
    extracted = OUT / "extracted"
    members = []
    with zipfile.ZipFile(DEST) as z:
        members = [{"name": i.filename, "size": i.file_size,
                    "compress_type": i.compress_type} for i in z.infolist()]
    extracted.mkdir(parents=True, exist_ok=True)
    methods = [
        ["bsdtar", "-xf", str(DEST), "-C", str(extracted)],
        ["7z", "x", "-y", f"-o{extracted}", str(DEST)],
        ["unzip", "-o", str(DEST), "-d", str(extracted)],
    ]
    errors = []
    for cmd in methods:
        if shutil.which(cmd[0]) is None:
            errors.append(f"{cmd[0]}: not installed"); continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and any(extracted.rglob("*")):
            print("extracted with", cmd[0]); break
        errors.append(f"{cmd[0]}: rc={r.returncode} {r.stderr.strip()[:200]}")
    else:
        raise SystemExit("all extraction backends failed: " + " | ".join(errors))
    (OUT / "inventory.json").write_text(json.dumps(
        {"source": URLS[0], "doi": "10.5281/zenodo.4034867", "md5": md5(DEST),
         "bytes": DEST.stat().st_size, "members": members}, indent=1))
    print(f"members: {len(members)}")
    for m in members:
        print(f"  {m['size']:>10d}  {m['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
