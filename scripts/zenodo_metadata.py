#!/usr/bin/env python3
"""Capture the Zenodo record metadata (size, checksum, licence) as evidence."""
from __future__ import annotations
import json, urllib.request
from pathlib import Path

OUT = Path("results"); OUT.mkdir(exist_ok=True)
url = "https://api.zenodo.org/api/records/4034867"
with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ctx/1.0"}),
                            timeout=120) as r:
    data = json.load(r)
files = [{"key": f.get("key"), "size": f.get("size"), "checksum": f.get("checksum"),
          "links": f.get("links", {})} for f in data.get("files", [])]
meta = {"id": data.get("id"), "doi": data.get("doi"),
        "title": (data.get("metadata", {}) or {}).get("title"),
        "license": (data.get("metadata", {}) or {}).get("license"),
        "access_right": (data.get("metadata", {}) or {}).get("access_right"),
        "publication_date": data.get("metadata", {}).get("publication_date"),
        "files": files, "fetched_from": url}
(OUT / "zenodo_record_metadata.json").write_text(json.dumps(meta, indent=1))
print(json.dumps(meta, indent=1)[:1500])
