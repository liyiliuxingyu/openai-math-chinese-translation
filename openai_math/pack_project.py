#!/usr/bin/env python3
"""Package the verified frozen project into a portable ZIP using only stdlib.

The existing project_manifest.json is required and is never regenerated here.
Only listed files plus the manifest itself are archived. The output must be
outside this project. Runtime/cache files and unlisted private helpers are not
included. No network, external application, or progress update is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

from verify_project import (ROOT, DEFAULT_MANIFEST, DEFAULT_STATE,
                            DEFAULT_EXCLUDES, ProjectError, is_excluded,
                            read_json, safe_path, sha256_file, verify_project)


ARCHIVE_ROOT = "OpenAI_math_project"


def package_project(output=None, compression=6):
    if not 0 <= compression <= 9:
        raise ProjectError("Compression level must be between 0 and 9")
    destination = Path(output).expanduser().resolve() if output else ROOT.parent / "OpenAI_math_project.zip"
    destination = destination.resolve()
    try:
        destination.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ProjectError("ZIP output must be outside the project root to protect its files")
    if destination.suffix.lower() != ".zip":
        raise ProjectError("--output must name a ZIP file, not a directory")
    if destination.exists() and not destination.is_file():
        raise ProjectError("ZIP output path is not a regular file")

    manifest_path = safe_path(ROOT, DEFAULT_MANIFEST)
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    verification = verify_project(ROOT, DEFAULT_MANIFEST, DEFAULT_STATE)
    if verification["result"] != "pass":
        raise ProjectError("Full project verification failed; run verify_project.py --json for details: " +
                           json.dumps(verification["errors"][:5], ensure_ascii=False))
    if manifest_path.read_bytes() != manifest_bytes:
        raise ProjectError("Manifest changed during verification; freeze the snapshot and try again")
    manifest = json.loads(manifest_bytes)
    entries = list(manifest["files"]) + [{"path": DEFAULT_MANIFEST,
                                           "size": len(manifest_bytes),
                                           "sha256": manifest_sha}]
    for row in entries:
        if is_excluded(row["path"], DEFAULT_EXCLUDES):
            raise ProjectError("Runtime/cache file must not appear in the archive manifest: " + row["path"])

    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".packing-", suffix=".zip.tmp", dir=destination.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    checksum_temporary = None
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=compression, allowZip64=True) as archive:
            for row in entries:
                source = safe_path(ROOT, row["path"])
                if source.is_symlink() or not source.is_file():
                    raise ProjectError("File is no longer a regular snapshot file: " + row["path"])
                digest = hashlib.sha256()
                actual_size = 0
                archive_name = ARCHIVE_ROOT + "/" + row["path"]
                with source.open("rb") as handle, archive.open(archive_name, "w", force_zip64=True) as member:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
                        actual_size += len(chunk)
                        member.write(chunk)
                if actual_size != row["size"] or digest.hexdigest() != row["sha256"]:
                    raise ProjectError("File changed after verification: " + row["path"])
        # Read back every compressed member to exercise ZIP CRC validation.
        with zipfile.ZipFile(temporary, "r") as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ProjectError("ZIP CRC validation failed: " + bad_member)
            if len(archive.infolist()) != len(entries):
                raise ProjectError("ZIP entry count differs from the verified manifest")
        archive_sha = sha256_file(temporary)
        archive_size = temporary.stat().st_size
        checksum_path = Path(str(destination) + ".sha256")
        # Stage both outputs before replacing a previous external ZIP.
        descriptor, checksum_name = tempfile.mkstemp(prefix=".packing-", suffix=".sha256.tmp", dir=destination.parent)
        checksum_temporary = Path(checksum_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(f"{archive_sha}  {destination.name}\n")
        os.replace(temporary, destination)
        os.replace(checksum_temporary, checksum_path)
    finally:
        temporary.unlink(missing_ok=True)
        if checksum_temporary is not None:
            checksum_temporary.unlink(missing_ok=True)
    return {"result": "packed", "output": str(destination),
            "checksum_file": str(checksum_path), "archive_root": ARCHIVE_ROOT,
            "file_count": len(entries), "manifest_listed_files": len(entries) - 1,
            "uncompressed_bytes": sum(row["size"] for row in entries),
            "zip_bytes": archive_size, "sha256": archive_sha,
            "manifest_sha256": manifest_sha, "compression_level": compression,
            "full_project_verification": "pass", "per_file_size_and_sha256": "pass",
            "zip_crc": "pass", "manifest_updated": False,
            "network_or_external_application_used": False,
            "scope": "Packages the verified existing snapshot; no new translation, semantic, visual, or mathematical-proof review."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="ZIP path outside the project; default: project parent/OpenAI_math_project.zip")
    parser.add_argument("--compression", type=int, default=6, help="DEFLATE compression level 0–9 (default 6)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = package_project(args.output, args.compression)
    except (ProjectError, OSError, ValueError, zipfile.BadZipFile) as exc:
        if args.json:
            print(json.dumps({"result": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Packed: {result['output']}")
        print(f"Files: {result['file_count']} (includes the manifest)")
        print(f"Uncompressed bytes: {result['uncompressed_bytes']}; ZIP bytes: {result['zip_bytes']}")
        print(f"SHA256: {result['sha256']}")
        print(f"Checksum file: {result['checksum_file']}")
        print("Project verification, per-file SHA256/size and ZIP CRC: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
