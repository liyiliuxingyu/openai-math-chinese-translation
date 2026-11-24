#!/usr/bin/env python3
"""Standard-library integrity and resource checks for the restored math project.

This verifies a snapshot and its references. It does not repeat historical
translation/visual reviews or validate the mathematical claims of the papers.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = "project_manifest.json"
DEFAULT_STATE = "handoff_state.json"
DEFAULT_EXCLUDES = ["runtime/", "__pycache__/", ".git/"]


class ProjectError(ValueError):
    pass


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectError(f"Cannot read JSON {path}: {exc}") from exc


def safe_path(root: Path, relative: str) -> Path:
    """Accept a portable relative path, and reject paths escaping the project."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ProjectError(f"Expected a nonempty POSIX relative path: {relative!r}")
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or ":" in p.parts[0]:
        raise ProjectError(f"Unsafe project-relative path: {relative!r}")
    target = root.joinpath(*p.parts)
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ProjectError(f"Path escapes the project, possibly through a symlink: {relative}") from exc
    return target


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_index(value) -> int:
    if isinstance(value, bool):
        raise ProjectError("A paper index cannot be a boolean")
    try:
        result = int(value)
    except (ValueError, TypeError) as exc:
        raise ProjectError(f"Invalid paper index: {value!r}") from exc
    if result < 1:
        raise ProjectError(f"Paper index must be positive: {value!r}")
    return result


def load_project_state(root: Path = ROOT, state_name: str = DEFAULT_STATE):
    path = safe_path(root, state_name)
    if path.exists():
        state = read_json(path)
        if not isinstance(state, dict):
            raise ProjectError("handoff_state.json must contain an object")
        return state, state_name
    # Read the restored historical progress and catalog without mutating them.
    progress_path = root / "math_translation/progress.json"
    catalog_path = root / "math_translation/source_catalog/catalog.json"
    if not progress_path.exists():
        raise ProjectError(f"Neither {state_name} nor math_translation/progress.json exists")
    progress = read_json(progress_path)
    if not isinstance(progress, dict):
        raise ProjectError("progress.json must contain an object")
    catalog = read_json(catalog_path) if catalog_path.exists() else []
    if isinstance(catalog, dict):
        catalog = next((catalog[k] for k in ("papers", "entries", "records", "items")
                        if isinstance(catalog.get(k), list)), [])
    if not isinstance(catalog, list):
        raise ProjectError("Catalog must be an array or an object containing one")
    completed_indices = set(progress.get("completed_sequences", []))
    records = []
    for item in catalog:
        index = item.get("sequence")
        if index not in completed_indices:
            continue
        index = normalize_index(index)
        directory = root / "math_translation/translated" / f"{index:04d}"
        candidates = []
        if directory.is_dir():
            for tex in directory.rglob("*.tex"):
                if re.search(r"\\documentclass(?:\[|\{)", tex.read_text(encoding="utf-8", errors="replace")):
                    candidates.append(tex)
        entry = candidates[0].relative_to(root).as_posix() if len(candidates) == 1 else None
        output = item.get("output_pdf")
        output = "output/" + Path(output).name if output else None
        records.append({"index": index,
                        "translation_dir": directory.relative_to(root).as_posix(),
                        "entrypoint": entry, "pdf": output,
                        "source_dir": f"math_translation/original/{index:04d}",
                        "source_pages": item.get("original_pages"),
                        "translated_pages": item.get("translated_pages")})
    next_index = progress.get("next_sequence")
    next_row = next((r for r in catalog if r.get("sequence") == next_index), {})
    next_dir = f"math_translation/original/{next_index:04d}" if isinstance(next_index, int) else None
    prepared = bool(next_dir and (root / next_dir).is_dir() and any((root / next_dir).rglob("*.tex")))
    next_translation = root / "math_translation/translated" / f"{next_index:04d}" if isinstance(next_index, int) else None
    translation_started = bool(next_translation and next_translation.is_dir() and any(next_translation.rglob("*.tex")))
    combined = progress.get("combined_pdf", {})
    combined_name = combined.get("filename") or Path(combined.get("path", "")).name
    state = {
        "schema_version": 1, "status": "progress_fallback_read_only",
        "source_commit": progress.get("source_commit"),
        "catalog_total": progress.get("catalog_manuscripts", len(catalog)),
        "family_count": progress.get("result_families"),
        "completed_count": progress.get("finished_papers"),
        "remaining_count": progress.get("remaining_current_catalog_papers"),
        "next_index": next_index, "next_title": progress.get("next_paper"),
        "next_source_prepared": prepared,
        "next_item": {"title_en": next_row.get("title_en"),
                      "title_zh": next_row.get("title_zh"), "source_dir": next_dir,
                      "source_prepared": prepared, "translation_started": translation_started,
                      "catalog_status": next_row.get("status")},
        "records": records, "progress": {"path": "math_translation/progress.json"},
        "combined": {"pdf": "output/" + combined_name if combined_name else None,
                     "pages": combined.get("pages")},
        "evidence_scope": "Historical progress and catalog records plus local path availability; no fresh semantic/visual review.",
        "_fallback_warning": "Read-only fallback; handoff_state.json is absent. Recorded Library version is not inferred.",
    }
    return state, "math_translation/progress.json + math_translation/source_catalog/catalog.json"


def state_records(state):
    records = state.get("records", [])
    if not isinstance(records, list):
        raise ProjectError("state.records must be an array")
    return records


def record_index(record):
    if not isinstance(record, dict):
        raise ProjectError("Each state.records item must be an object")
    for name in ("index", "paper_index", "number", "id"):
        if name in record:
            return normalize_index(record[name])
    raise ProjectError("Paper record has no index")


def is_excluded(relative: str, exclusions) -> bool:
    # Prefixes, not executable patterns. __pycache__ may occur at any depth.
    parts = PurePosixPath(relative).parts
    for excluded in exclusions:
        if excluded == "__pycache__/" and "__pycache__" in parts:
            return True
        if excluded.endswith("/"):
            if relative.startswith(excluded):
                return True
        elif relative == excluded:
            return True
    return False


def inventory(root: Path, manifest_name: str, exclusions):
    files, symlinks = [], []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == manifest_name or is_excluded(relative, exclusions):
            continue
        if path.is_symlink():
            symlinks.append(relative)
        elif path.is_file():
            files.append(path)
    return files, symlinks


def create_manifest(root: Path, manifest_name: str):
    manifest_path = safe_path(root, manifest_name)
    files, symlinks = inventory(root, manifest_name, DEFAULT_EXCLUDES)
    if symlinks:
        raise ProjectError("Snapshot requires regular portable files; unresolved symlinks: " + ", ".join(symlinks))
    data = {
        "schema_version": 1,
        "hash_algorithm": "sha256",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_self_excluded": manifest_name,
        "excluded_paths": DEFAULT_EXCLUDES,
        "scope": "All regular snapshot files except this manifest and explicitly excluded runtime/cache paths.",
        "files": [{"path": p.relative_to(root).as_posix(), "size": p.stat().st_size,
                   "sha256": sha256_file(p)} for p in files],
    }
    data["file_count"] = len(data["files"])
    data["total_bytes"] = sum(row["size"] for row in data["files"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"result": "created", "manifest": manifest_name,
            "file_count": data["file_count"], "total_bytes": data["total_bytes"]}


def verify_manifest(root: Path, manifest_name: str):
    data = read_json(safe_path(root, manifest_name))
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        raise ProjectError("Manifest must contain a files array")
    if data.get("hash_algorithm", "sha256") != "sha256":
        raise ProjectError("Only SHA256 manifests are supported")
    exclusions = data.get("excluded_paths", DEFAULT_EXCLUDES)
    if not isinstance(exclusions, list) or not all(isinstance(x, str) for x in exclusions):
        raise ProjectError("Manifest excluded_paths must be an array of path prefixes")
    errors, seen = [], set()
    checked = 0
    for row in data["files"]:
        if not isinstance(row, dict):
            errors.append({"code": "invalid_manifest_row", "detail": repr(row)})
            continue
        name = row.get("path")
        try:
            path = safe_path(root, name)
        except ProjectError as exc:
            errors.append({"code": "unsafe_manifest_path", "detail": str(exc)})
            continue
        if name in seen:
            errors.append({"code": "duplicate_manifest_path", "path": name})
            continue
        seen.add(name)
        if name == manifest_name or is_excluded(name, exclusions):
            errors.append({"code": "excluded_file_listed", "path": name})
        expected_hash = row.get("sha256", "")
        if not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None:
            errors.append({"code": "invalid_sha256", "path": name})
            continue
        if not isinstance(row.get("size"), int) or isinstance(row.get("size"), bool) or row["size"] < 0:
            errors.append({"code": "invalid_size", "path": name})
            continue
        if path.is_symlink():
            errors.append({"code": "symlink_in_snapshot", "path": name})
        elif not path.is_file():
            errors.append({"code": "missing_file", "path": name})
        else:
            actual_size = path.stat().st_size
            actual_hash = sha256_file(path)
            checked += 1
            if actual_size != row["size"]:
                errors.append({"code": "size_mismatch", "path": name,
                               "expected": row["size"], "actual": actual_size})
            if actual_hash != expected_hash:
                errors.append({"code": "sha256_mismatch", "path": name,
                               "expected": expected_hash, "actual": actual_hash})
    files, symlinks = inventory(root, manifest_name, exclusions)
    actual_names = {p.relative_to(root).as_posix() for p in files}
    for name in sorted(actual_names - seen):
        errors.append({"code": "unlisted_file", "path": name})
    for name in symlinks:
        errors.append({"code": "unlisted_symlink", "path": name})
    if "file_count" in data and data["file_count"] != len(data["files"]):
        errors.append({"code": "manifest_file_count_mismatch"})
    if "total_bytes" in data and all(isinstance(r, dict) and isinstance(r.get("size"), int) for r in data["files"]):
        if data["total_bytes"] != sum(r["size"] for r in data["files"]):
            errors.append({"code": "manifest_total_bytes_mismatch"})
    return {"checked_files": checked, "listed_files": len(data["files"]),
            "excluded_paths": exclusions, "errors": errors}


def check_state(root: Path, state):
    errors, warnings = [], []
    records = state_records(state)
    indices = []
    for record in records:
        try:
            index = record_index(record)
            indices.append(index)
        except ProjectError as exc:
            errors.append({"code": "invalid_record", "detail": str(exc)})
            continue
        for key in ("translation_dir", "entrypoint", "pdf"):
            value = record.get(key)
            if not value:
                errors.append({"code": "missing_record_field", "index": index, "field": key})
                continue
            try:
                path = safe_path(root, value)
                exists = path.is_dir() if key == "translation_dir" else path.is_file()
                if not exists:
                    errors.append({"code": "missing_record_path", "index": index,
                                   "field": key, "path": value})
            except ProjectError as exc:
                errors.append({"code": "unsafe_record_path", "index": index, "detail": str(exc)})
        if record.get("source_dir"):
            try:
                if not safe_path(root, record["source_dir"]).is_dir():
                    errors.append({"code": "missing_source_dir", "index": index,
                                   "path": record["source_dir"]})
            except ProjectError as exc:
                errors.append({"code": "unsafe_source_dir", "index": index, "detail": str(exc)})
    completed = state.get("completed_count")
    if not isinstance(completed, int) or completed != len(records):
        errors.append({"code": "completed_count_mismatch", "state": completed,
                       "records": len(records)})
    if len(indices) != len(set(indices)):
        errors.append({"code": "duplicate_paper_indices"})
    if isinstance(completed, int) and sorted(indices) != list(range(1, completed + 1)):
        errors.append({"code": "noncontiguous_completed_indices", "indices": sorted(indices)})
    if isinstance(completed, int) and state.get("next_index") != completed + 1:
        errors.append({"code": "next_index_mismatch"})
    total, remaining = state.get("catalog_total"), state.get("remaining_count")
    if not all(isinstance(v, int) for v in (total, completed, remaining)) or total - completed != remaining:
        errors.append({"code": "remaining_count_mismatch"})
    commit = state.get("source_commit", "")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        errors.append({"code": "invalid_fixed_source_commit"})
    for container, field in (("progress", "path"), ("combined", "pdf")):
        info = state.get(container, {})
        value = info.get(field) if isinstance(info, dict) else None
        if not value:
            errors.append({"code": "missing_state_field", "field": f"{container}.{field}"})
        else:
            try:
                if not safe_path(root, value).is_file():
                    errors.append({"code": "missing_state_path", "path": value})
            except ProjectError as exc:
                errors.append({"code": "unsafe_state_path", "detail": str(exc)})
    # The handoff summary must agree with the restored canonical progress and
    # catalog, not merely be internally arithmetically consistent.
    progress_info = state.get("progress", {})
    if isinstance(progress_info, dict) and progress_info.get("path"):
        try:
            progress = read_json(safe_path(root, progress_info["path"]))
            field_pairs = {"source_commit": "source_commit", "catalog_total": "catalog_manuscripts",
                           "family_count": "result_families", "completed_count": "finished_papers",
                           "remaining_count": "remaining_current_catalog_papers", "next_index": "next_sequence"}
            for state_key, progress_key in field_pairs.items():
                if progress_key in progress and state.get(state_key) != progress[progress_key]:
                    errors.append({"code": "canonical_progress_mismatch", "field": state_key,
                                   "state": state.get(state_key), "progress": progress[progress_key]})
            if "completed_sequences" in progress and sorted(indices) != sorted(progress["completed_sequences"]):
                errors.append({"code": "canonical_completed_indices_mismatch"})
        except (ProjectError, OSError) as exc:
            errors.append({"code": "canonical_progress_unreadable", "detail": str(exc)})
    catalog_info = state.get("catalog", {})
    catalog_name = catalog_info.get("path", "math_translation/source_catalog/catalog.json") if isinstance(catalog_info, dict) else "math_translation/source_catalog/catalog.json"
    catalog_path = safe_path(root, catalog_name)
    if catalog_path.exists():
        try:
            catalog = read_json(catalog_path)
            if isinstance(catalog, list):
                if len(catalog) != total:
                    errors.append({"code": "canonical_catalog_count_mismatch", "actual": len(catalog), "state": total})
                completed_catalog = sorted(r["sequence"] for r in catalog if r.get("status") == "complete")
                if completed_catalog != sorted(indices):
                    errors.append({"code": "canonical_catalog_completion_mismatch", "catalog": completed_catalog})
            else:
                errors.append({"code": "canonical_catalog_invalid_format"})
        except ProjectError as exc:
            errors.append({"code": "canonical_catalog_unreadable", "detail": str(exc)})
    # Cross-check embedded hashes as well as the separate all-files manifest.
    hash_bindings = []
    for r in records:
        for path_key, hash_key in (("entrypoint", "entrypoint_sha256"), ("pdf", "pdf_sha256"), ("source_pdf", "source_pdf_sha256")):
            if r.get(path_key) and r.get(hash_key):
                hash_bindings.append((r[path_key], r[hash_key]))
    for container, path_key in (("catalog", "path"), ("progress", "path"), ("combined", "pdf")):
        info = state.get(container, {})
        if isinstance(info, dict) and info.get(path_key) and info.get("sha256"):
            hash_bindings.append((info[path_key], info["sha256"]))
    for name, expected in hash_bindings:
        try:
            path = safe_path(root, name)
            if path.is_file() and sha256_file(path) != expected:
                errors.append({"code": "state_embedded_sha256_mismatch", "path": name})
        except (ProjectError, OSError) as exc:
            errors.append({"code": "state_hash_check_error", "path": name, "detail": str(exc)})
    page_counts = [r.get("translated_pages") for r in records]
    combined = state.get("combined", {})
    if records and all(isinstance(n, int) and n > 0 for n in page_counts):
        if combined.get("pages") != sum(page_counts):
            errors.append({"code": "combined_page_record_sum_mismatch",
                           "record_sum": sum(page_counts), "combined_record": combined.get("pages")})
    else:
        warnings.append({"code": "page_count_not_summed", "detail": "Some per-paper page records are absent; PDF contents are not parsed by this standard-library checker."})
    return {"completed_records": len(records), "indices": sorted(indices),
            "errors": errors, "warnings": warnings,
            "page_count_scope": "Record arithmetic only; PDF byte integrity is checked by SHA256, not a new page-layout review."}


RESOURCE = re.compile(
    r"\\(input|include|subfile|bibliography|addbibresource|includegraphics\*?|includepdf|lstinputlisting|verbatiminput)"
    r"\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}", re.S)
SYSTEM_RESOURCE = re.compile(r"\\(usepackage|RequirePackage|documentclass|bibliographystyle)\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}")


def strip_comments(text):
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def tex_resource_check(root: Path, records):
    errors, warnings, external = [], [], set()
    scanned, references = set(), []
    for record in records:
        if not record.get("entrypoint"):
            continue
        try:
            entry = safe_path(root, record["entrypoint"])
        except ProjectError:
            continue
        if not entry.is_file():
            continue
        # TeX interprets ordinary relative inputs from its working directory.
        # File-local paths are also accepted for sources using import-like layouts.
        base = entry.parent
        queue = [entry]
        per_entry_seen = set()
        graphics_dirs = []
        while queue:
            tex = queue.pop()
            if tex in per_entry_seen:
                continue
            per_entry_seen.add(tex)
            scanned.add(tex.relative_to(root).as_posix())
            try:
                text = strip_comments(tex.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                errors.append({"code": "unreadable_tex", "path": str(tex.relative_to(root)), "detail": str(exc)})
                continue
            for gp in re.finditer(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)+)\}", text):
                graphics_dirs.extend(re.findall(r"\{([^{}]*)\}", gp.group(1)))
            for command, names in SYSTEM_RESOURCE.findall(text):
                suffix = {"documentclass": ".cls", "bibliographystyle": ".bst"}.get(command, ".sty")
                for name in names.split(","):
                    name = name.strip()
                    local = base / (name if Path(name).suffix else name + suffix)
                    if local.is_file():
                        try:
                            local.resolve().relative_to(root.resolve())
                        except ValueError:
                            errors.append({"code": "external_local_tex_resource", "name": name})
                            continue
                        scanned.add(local.resolve().relative_to(root.resolve()).as_posix())
                        if local.suffix in (".sty", ".cls"):
                            queue.append(local.resolve())
                    else:
                        external.add((command, name + ("" if Path(name).suffix else suffix)))
            for match in RESOURCE.finditer(text):
                command, argument = match.groups()
                for name in (argument.split(",") if command == "bibliography" else [argument]):
                    name = name.strip()
                    where = {"from": tex.relative_to(root).as_posix(),
                             "line": text[:match.start()].count("\n") + 1,
                             "command": command, "argument": name}
                    if "\\" in name or "#" in name or name.startswith(("http:", "https:")):
                        warnings.append({"code": "dynamic_tex_reference_not_resolved", **where})
                        continue
                    if Path(name).is_absolute() or ".." in PurePosixPath(name).parts:
                        # Parent-relative paths may be valid inside the project.
                        candidates = [base / name, tex.parent / name]
                    else:
                        candidates = [base / name, tex.parent / name]
                        if command.startswith("includegraphics"):
                            candidates.extend(base / directory / name for directory in graphics_dirs)
                    suffixes = [""] if Path(name).suffix else (
                        ["", ".tex"] if command in ("input", "include", "subfile") else
                        ["", ".bib"] if command in ("bibliography", "addbibresource") else
                        ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".mps"] if command.startswith("includegraphics") else [""])
                    found = None
                    for candidate in candidates:
                        for suffix in suffixes:
                            possible = Path(str(candidate) + suffix)
                            try:
                                possible.resolve().relative_to(root.resolve())
                            except ValueError:
                                continue
                            if possible.is_file():
                                found = possible.resolve()
                                break
                        if found is not None:
                            break
                    if found is None:
                        errors.append({"code": "missing_tex_resource", **where})
                    else:
                        references.append({**where, "resolved": found.relative_to(root).as_posix()})
                        if command in ("input", "include", "subfile") and found.suffix == ".tex":
                            queue.append(found)
    return {"scanned_tex_or_local_style_files": len(scanned), "resolved_reference_count": len(references),
            "references": references, "external_tex_resources": [{"command": c, "name": n} for c, n in sorted(external)],
            "errors": errors, "warnings": warnings,
            "scope": "Static literal references reachable from completed-paper entrypoints. External TeX packages/classes/styles are reported for doctor, not treated as missing project files."}


def verify_project(root: Path, manifest_name: str, state_name: str):
    manifest = verify_manifest(root, manifest_name)
    state, state_source = load_project_state(root, state_name)
    structure = check_state(root, state)
    resources = tex_resource_check(root, state_records(state))
    errors = manifest["errors"] + structure["errors"] + resources["errors"]
    warnings = structure["warnings"] + resources["warnings"]
    return {"result": "pass" if not errors else "failed", "manifest": manifest_name,
            "state_source": state_source, "manifest_check": manifest,
            "state_check": structure, "tex_resource_check": resources,
            "errors": errors, "warnings": warnings,
            "evidence_scope": "This run verifies restored snapshot bytes, recorded counts and resource paths only; historical semantic/visual reports remain historical and mathematical claims are not independently validated."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--state", default=DEFAULT_STATE)
    parser.add_argument("--json", action="store_true", help="Print the full machine-readable result")
    parser.add_argument("--create-manifest", action="store_true", help="Explicitly create/replace the snapshot manifest; run only after assembling the package")
    args = parser.parse_args(argv)
    try:
        result = create_manifest(ROOT, args.manifest) if args.create_manifest else verify_project(ROOT, args.manifest, args.state)
    except (ProjectError, OSError) as exc:
        if args.json:
            print(json.dumps({"result": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.create_manifest:
        print(f"Created {result['manifest']}: {result['file_count']} files, {result['total_bytes']} bytes.")
    else:
        print(f"Verification: {result['result'].upper()}")
        print(f"SHA256 checked: {result['manifest_check']['checked_files']} files")
        print(f"Completed records: {result['state_check']['completed_records']}")
        print(f"TeX resources resolved: {result['tex_resource_check']['resolved_reference_count']}")
        for issue in result["errors"] + result["warnings"]:
            print(json.dumps(issue, ensure_ascii=False))
        print(result["evidence_scope"])
    return 0 if result["result"] in ("pass", "created") else 1


if __name__ == "__main__":
    raise SystemExit(main())
