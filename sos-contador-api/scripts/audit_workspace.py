#!/usr/bin/env python3
"""Inventory a workspace without moving or deleting anything.

Reports contain private paths and must be written outside the inspected tree.
The inventory is evidence for a human-reviewed cleanup, never an allowlist to delete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def inventory(root: Path) -> dict:
    root = root.resolve(strict=True)
    files = []
    skipped = []
    errors = []

    def onerror(error):
        errors.append({"path": str(error.filename), "error": type(error).__name__})

    for current, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        parent = Path(current)
        for name in list(dirs):
            path = parent / name
            if name == ".git" or path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                skipped.append(str(path.relative_to(root)))
                dirs.remove(name)
        for name in sorted(names):
            path = parent / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                skipped.append(relative)
                continue
            try:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                stat = path.stat()
                files.append({"path": relative, "bytes": stat.st_size,
                              "sha256": digest.hexdigest(), "mtime_ns": stat.st_mtime_ns})
            except OSError as error:
                errors.append({"path": relative, "error": type(error).__name__})
    return {"root": str(root), "created_at": datetime.now(timezone.utc).isoformat(),
            "files": sorted(files, key=lambda item: item["path"]),
            "skipped": sorted(skipped), "errors": errors,
            "notice": "Inventario de solo lectura. No autoriza borrados ni clasifica documentación por su nombre."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.out.expanduser().resolve()
    if output.is_relative_to(root):
        parser.error("El inventario privado debe guardarse fuera del árbol inspeccionado.")
    if output.exists():
        parser.error("El destino ya existe; no se sobrescribe.")
    report = inventory(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    counts = Counter(Path(item["path"]).parts[0] for item in report["files"])
    print(json.dumps({"counts": counts, "errors": len(report["errors"]),
                      "skipped": len(report["skipped"]), "written_to": str(output)}, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
