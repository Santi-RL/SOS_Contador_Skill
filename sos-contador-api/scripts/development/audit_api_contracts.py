#!/usr/bin/env python3
"""Comparar una colección Postman descargada con el catálogo, sin red ni mutaciones."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit


def walk_requests(items):
    for item in items:
        if "item" in item:
            yield from walk_requests(item["item"])
        elif isinstance(item.get("request"), dict):
            yield item["request"]
        else:
            raise ValueError("Elemento Postman sin request estructurada")


def field_paths(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            path = prefix + key
            yield path
            yield from field_paths(child, path + ".")
    elif isinstance(value, list):
        for child in value:
            yield from field_paths(child, prefix + "[].")


def request_contract(request):
    url = request.get("url", "")
    obj = url if isinstance(url, dict) else request.get("urlObject", {})
    raw = obj.get("raw", "") if isinstance(url, dict) else url
    if "/api-comunidad/" not in raw:
        raise ValueError("URL fuera del prefijo de API esperado")
    route = raw.split("/api-comunidad/", 1)[1]
    # Postman también usa ? como marcador de parámetro opcional en un path.
    if route.endswith("?") and re.search(r"/:[^/?]+\?$", route):
        path = route
    else:
        path = route.split("?", 1)[0]
    if "query" in obj:
        query = sorted({q["key"] for q in obj["query"] if q.get("key") and not q.get("disabled")})
    else:
        query = sorted({k for k, _ in parse_qsl(urlsplit(raw).query, keep_blank_values=True)})
    body = request.get("body") or {}
    raw_body = body.get("raw", "").strip()
    fields, body_parse = [], "empty"
    if raw_body:
        try:
            fields = sorted(set(field_paths(json.loads(raw_body))))
            body_parse = "json"
        except json.JSONDecodeError:
            body_parse = "not-json"
    elif body.get("mode") in {"urlencoded", "formdata"}:
        fields = sorted({f["key"] for f in body.get(body["mode"], []) if f.get("key")})
        body_parse = body["mode"]
    # No devolver valores de body, ejemplos, tokens ni cabeceras.
    return {"method": request["method"].upper(), "path": path, "query": query,
            "auth_type": (request.get("auth") or {}).get("type", "unspecified"),
            "body_parse": body_parse, "body_fields": fields}


def compare(collection, catalog):
    contracts = [request_contract(r) for r in walk_requests(collection["item"])]
    operations = catalog["operations"]
    key = lambda x: (x["method"], x["path"].rstrip("?"))
    published_counts = Counter(key(c) for c in contracts)
    local_counts = Counter(key(c) for c in operations)
    missing = [{"method": method, "path": path, "count": count}
               for (method, path), count in (published_counts - local_counts).items()]
    local_only = [{"method": method, "path": path, "count": count}
                  for (method, path), count in (local_counts - published_counts).items()]
    query_differences, optional_id_variants = [], []
    for contract in contracts:
        for operation in operations:
            if key(contract) != key(operation):
                continue
            if set(contract["query"]) != set(operation["query"]):
                query_differences.append({"id": operation["id"], "published": contract["query"], "catalog": operation["query"]})
            if contract["path"] != operation["path"]:
                optional_id_variants.append({"id": operation["id"], "published": contract["path"], "catalog": operation["path"]})
    return {"published_requests": len(contracts), "catalog_operations": len(operations),
            "unique_method_paths": len(published_counts), "missing_from_catalog": missing,
            "catalog_only": local_only, "query_differences": query_differences,
            "optional_path_variants": optional_id_variants, "contracts": contracts,
            "limits": "Compara rutas, multiplicidad y queries; enumera campos de ejemplos, sin validar su semántica, autenticación, obligatoriedad ni comportamiento real."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-mode", required=True, choices=["development"])
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parents[2] / "references/public-api-operations.json")
    args = parser.parse_args(argv)
    report = compare(json.loads(args.collection.read_text(encoding="utf-8-sig")),
                     json.loads(args.catalog.read_text(encoding="utf-8-sig")))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(report["missing_from_catalog"] or report["catalog_only"] or report["query_differences"]))


if __name__ == "__main__":
    raise SystemExit(main())
