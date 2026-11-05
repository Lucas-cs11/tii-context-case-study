#!/usr/bin/env python3
"""Capture Zenodo record metadata (size, checksum, licence); never fatal."""
from __future__ import annotations
import json, ssl, urllib.error, urllib.request
from pathlib import Path

OUT = Path("results"); OUT.mkdir(exist_ok=True)
URLS = ["https://api.zenodo.org/api/records/4034867",
        "https://zenodo.org/api/records/4034867",
        "https://zenodo.org/records/4034867"]
attempts = []
meta = {}
for url in URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "context-case-study/1.0",
                                                   "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
            raw = r.read()
        attempts.append({"url": url, "status": "ok", "bytes": len(raw)})
        try:
            data = json.loads(raw)
        except Exception:
            meta = {"raw_html_head": raw[:400].decode("utf-8", "replace")}
            break
        files = [{"key": f.get("key"), "size": f.get("size"), "checksum": f.get("checksum")}
                 for f in data.get("files", [])]
        m = data.get("metadata", {}) or {}
        meta = {"id": data.get("id"), "doi": data.get("doi"), "title": m.get("title"),
                "license": m.get("license"), "access_right": m.get("access_right"),
                "publication_date": m.get("publication_date"), "files": files,
                "fetched_from": url}
        break
    except Exception as exc:  # noqa: BLE001
        attempts.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
meta["attempts"] = attempts
(OUT / "zenodo_record_metadata.json").write_text(json.dumps(meta, indent=1))
print(json.dumps(meta, indent=1)[:1200])
