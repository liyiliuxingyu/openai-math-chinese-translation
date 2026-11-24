#!/usr/bin/env python3
"""Portable read-only status/next/doctor and isolated rebuild commands.

All project paths are resolved relative to this file, not the current directory.
A rebuild writes only runtime/build/<paper>/ and does not replace delivered PDFs,
translated sources, historical QA, catalog entries, or progress records.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from verify_project import (ROOT, DEFAULT_STATE, ProjectError, load_project_state,
                            read_json, safe_path, sha256_file, state_records, record_index,
                            tex_resource_check)

try:
    from portable_tex import build_environment
except ImportError:
    def build_environment(root):
        return os.environ.copy()


REQUIRED_TEX_FILES = [
    "xelatex.fmt", "ctexart.cls", "xeCJK.sty", "fontspec.sty", "amsmath.sty",
    "amssymb.sty", "amsthm.sty", "geometry.sty", "hyperref.sty",
    "FandolSong-Regular.otf",
]
OPTIONAL_COMMANDS = ["pdftoppm", "pdftotext", "pdfinfo", "fc-match"]


def run_probe(argv, timeout=15, env=None, cwd=None):
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           env=env, cwd=cwd)
        return {"returncode": p.returncode, "stdout": p.stdout.strip(),
                "stderr": p.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc)}


def doctor(compile_probe=False, state_name=DEFAULT_STATE):
    env = build_environment(ROOT)
    commands = {}
    for name in ["xelatex", "bibtex", "kpsewhich"] + OPTIONAL_COMMANDS:
        path = shutil.which(name)
        info = {"path": path, "binary_found": path is not None,
                "required_for_rebuild": name in ("xelatex", "bibtex", "kpsewhich")}
        if path and name in ("xelatex", "bibtex", "kpsewhich"):
            version = run_probe([path, "--version"], env=env)
            info["version_first_line"] = (version["stdout"] or version["stderr"]).splitlines()[:1]
            info["version_probe_returncode"] = version["returncode"]
        commands[name] = info
    resources = []
    kpse = commands["kpsewhich"]["path"]
    resource_names = set(REQUIRED_TEX_FILES)
    resource_scan_error = None
    try:
        state, _ = load_project_state(ROOT, state_name)
        resource_names.update(r["name"] for r in tex_resource_check(ROOT, state_records(state))["external_tex_resources"])
    except (ProjectError, OSError) as exc:
        resource_scan_error = str(exc)
    for name in sorted(resource_names):
        arguments = [kpse, "--engine=xetex", name] if name == "xelatex.fmt" else [kpse, name]
        p = run_probe(arguments, env=env) if kpse else {"returncode": None, "stdout": "", "stderr": "kpsewhich is not available"}
        found = p["returncode"] == 0 and bool(p["stdout"])
        resources.append({"name": name, "found": found,
                          "resolved_path": p["stdout"] if found else None,
                          "lookup_error": p["stderr"] or None})
    broken_databases = []
    for candidate in [Path("/usr/share/texlive/texmf-dist/ls-R"), Path("/usr/share/texmf/ls-R")]:
        if candidate.is_symlink() and not candidate.exists():
            broken_databases.append({"path": str(candidate), "target": os.readlink(candidate)})
    optional_python = {}
    for module in ["pymupdf", "fitz", "pypdf", "PIL"]:
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        optional_python[module] = {"available": found,
                                   "needed_for_status_or_verify": False,
                                   "purpose": "Optional PDF rendering, page-count or image inspection workflows"}
    binaries_ready = all(commands[n]["binary_found"] for n in ("xelatex", "bibtex", "kpsewhich"))
    resources_ready = all(r["found"] for r in resources)
    result = {"python": {"version": sys.version.split()[0], "executable": sys.executable,
                          "status_verify_dependencies": "Python standard library only"},
              "commands": commands, "tex_resources": resources,
              "broken_tex_filename_databases": broken_databases,
              "optional_python": optional_python,
              "tex_environment": {k: env[k] for k in ("TEXMF", "TEXMFHOME", "TEXMFVAR", "TEXMFCONFIG") if k in env},
              "resource_scan_error": resource_scan_error,
              "compile_ready": binaries_ready and resources_ready,
              "network_or_installation_attempted": False,
              "scope": "Read-only availability checks. Binary discovery alone is not proof that TeX can compile Chinese papers. A complete historical build is not repeated by doctor."}
    if compile_probe:
        out = ROOT / "runtime/doctor"
        out.mkdir(parents=True, exist_ok=True)
        source = out / "probe.tex"
        source.write_text("\\documentclass{ctexart}\n\\usepackage{amsmath}\n\\begin{document}\n中文编译检查。$x^2+1=0$\n\\end{document}\n", encoding="utf-8")
        if commands["xelatex"]["path"]:
            if (out / "probe.pdf").exists():
                (out / "probe.pdf").unlink()
            probe = run_probe([commands["xelatex"]["path"], "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "probe.tex"], timeout=90, cwd=out, env=env)
            (out / "probe_command.log").write_text(probe["stdout"] + "\n" + probe["stderr"], encoding="utf-8")
            actual_pass = probe["returncode"] == 0 and (out / "probe.pdf").is_file()
            result["compile_probe"] = {"result": "pass" if actual_pass else "failed",
                                       "returncode": probe["returncode"],
                                       "log": "runtime/doctor/probe_command.log",
                                       "scope": "One minimal Chinese/math document, not the complete translation corpus"}
            result["compile_ready"] = binaries_ready and resources_ready and actual_pass
        else:
            result["compile_probe"] = {"result": "not_run", "reason": "xelatex binary missing"}
    result["result"] = "ready" if result["compile_ready"] else "dependencies_missing"
    return result


def status(state_name=DEFAULT_STATE):
    state, source = load_project_state(ROOT, state_name)
    records = state_records(state)
    rows = []
    for r in records:
        row = {"index": record_index(r), "entrypoint": r.get("entrypoint"),
               "pdf": r.get("pdf"), "translated_pages": r.get("translated_pages")}
        row["entrypoint_present"] = bool(r.get("entrypoint") and safe_path(ROOT, r["entrypoint"]).is_file())
        row["pdf_present"] = bool(r.get("pdf") and safe_path(ROOT, r["pdf"]).is_file())
        rows.append(row)
    return {"result": "ok", "state_source": source, "project_status": state.get("status"),
            "source_commit": state.get("source_commit"),
            "catalog_total": state.get("catalog_total"), "family_count": state.get("family_count"),
            "completed_count": state.get("completed_count"), "records_found": len(rows),
            "remaining_count": state.get("remaining_count"), "next_index": state.get("next_index"),
            "next_title": state.get("next_title"), "progress": state.get("progress"),
            "next_source_prepared": state.get("next_source_prepared"),
            "next_translation_started": state.get("next_item", {}).get("translation_started"),
            "combined": state.get("combined"), "records": rows,
            "evidence_scope": state.get("evidence_scope", "Restored records only; no fresh semantic, visual or mathematical verification is implied."),
            "warning": state.get("_fallback_warning")}


def next_item(state_name=DEFAULT_STATE):
    state, source = load_project_state(ROOT, state_name)
    item = state.get("next_item") if isinstance(state.get("next_item"), dict) else {}
    index = state.get("next_index")
    prepared = item.get("source_prepared", state.get("next_source_prepared", False))
    return {"result": "ok", "state_source": source, "index": index,
            "title": state.get("next_title"), **item,
            "source_prepared": prepared,
            "status_summary_zh": ("原文已齐" if prepared else "原文尚未齐备") + "／" + ("翻译已开始" if item.get("translation_started") else "翻译未开始"),
            "source_commit": state.get("source_commit"),
            "read_only": True,
            "instruction": "Inspect the fixed catalog entry and source provenance before starting. This command does not download, translate, update progress, or mark the next paper complete."}


def resolve_paper(index: int, state_name=DEFAULT_STATE):
    state, _ = load_project_state(ROOT, state_name)
    matches = [r for r in state_records(state) if record_index(r) == index]
    if len(matches) != 1:
        raise ProjectError(f"No unique completed-paper record for {index:04d}. This command rebuilds restored completed papers only.")
    record = matches[0]
    if not record.get("entrypoint"):
        raise ProjectError(f"Paper {index:04d} has no recorded TeX entrypoint")
    entry = safe_path(ROOT, record["entrypoint"])
    if not entry.is_file() or entry.suffix.lower() != ".tex":
        raise ProjectError(f"Missing TeX entrypoint: {record['entrypoint']}")
    translation_dir = safe_path(ROOT, record.get("translation_dir", entry.parent.relative_to(ROOT).as_posix()))
    try:
        entry.resolve().relative_to(translation_dir.resolve())
    except ValueError as exc:
        raise ProjectError("Entrypoint is outside its recorded translation directory") from exc
    return record, entry


def build(index: int, state_name=DEFAULT_STATE, out_name=None, passes=4, dry_run=False):
    record, entry = resolve_paper(index, state_name)
    out_name = out_name or f"runtime/build/{index:04d}"
    out = safe_path(ROOT, out_name)
    try:
        out.resolve().relative_to((ROOT / "runtime").resolve())
    except ValueError as exc:
        raise ProjectError("Build output must stay under runtime/ to protect delivered PDFs and historical QA") from exc
    if passes < 2 or passes > 6:
        raise ProjectError("XeLaTeX pass count must be between 2 and 6")
    tex_cmd = [shutil.which("xelatex") or "xelatex", "-no-shell-escape",
               "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
               f"-output-directory={out}", entry.name]
    bib_cmd = [shutil.which("bibtex") or "bibtex", entry.stem]
    plan = {"result": "planned", "paper_index": index,
            "entrypoint": entry.relative_to(ROOT).as_posix(), "working_directory": entry.parent.relative_to(ROOT).as_posix(),
            "output_directory": out.relative_to(ROOT).as_posix(),
            "xelatex_passes": passes, "commands": {"xelatex": tex_cmd, "bibtex_if_aux_has_bibdata": bib_cmd},
            "historical_outputs_overwritten": False,
            "network_or_installation_attempted": False}
    if dry_run:
        return plan
    readiness = doctor(state_name=state_name)
    if not readiness["compile_ready"]:
        return {**plan, "result": "dependencies_missing", "doctor": readiness,
                "message": "Rebuild not started. See dependency instructions; no downloads or silent environment repair were attempted."}
    out.mkdir(parents=True, exist_ok=True)
    # Clear only a previously generated output PDF so a stale file cannot pass.
    output_pdf = out / f"{entry.stem}.pdf"
    if output_pdf.exists():
        output_pdf.unlink()
    env = build_environment(ROOT)
    # Trailing path separator preserves kpathsea's default search locations.
    for key in ("TEXINPUTS", "BIBINPUTS", "BSTINPUTS"):
        env[key] = str(entry.parent) + "//" + os.pathsep + env.get(key, "")
    commands = []
    for number in range(1, passes + 1):
        log_file = out / f"xelatex_pass_{number}.log"
        with log_file.open("w", encoding="utf-8") as log:
            proc = subprocess.run(tex_cmd, cwd=entry.parent, env=env,
                                  stdout=log, stderr=subprocess.STDOUT, text=True)
        commands.append({"kind": "xelatex", "pass": number, "returncode": proc.returncode,
                         "log": log_file.relative_to(ROOT).as_posix()})
        if proc.returncode:
            result = {**plan, "result": "failed", "commands_executed": commands,
                      "message": "XeLaTeX failed; inspect the recorded log."}
            break
        if number == 1:
            aux = out / f"{entry.stem}.aux"
            if aux.exists() and "\\bibdata{" in aux.read_text(encoding="utf-8", errors="replace"):
                bib_log = out / "bibtex_command.log"
                with bib_log.open("w", encoding="utf-8") as log:
                    proc = subprocess.run(bib_cmd, cwd=out, env=env,
                                          stdout=log, stderr=subprocess.STDOUT, text=True)
                commands.append({"kind": "bibtex", "returncode": proc.returncode,
                                 "log": bib_log.relative_to(ROOT).as_posix()})
                if proc.returncode:
                    result = {**plan, "result": "failed", "commands_executed": commands,
                              "message": "BibTeX failed; inspect the recorded log."}
                    break
    else:
        result = {**plan, "result": "built" if output_pdf.is_file() else "failed",
                  "commands_executed": commands}
        if output_pdf.is_file():
            result["output_pdf"] = output_pdf.relative_to(ROOT).as_posix()
            result["output_pdf_sha256"] = sha256_file(output_pdf)
            result["warning"] = "Compilation is not translation review or visual QA. Rebuilt PDF bytes may differ from historical output because of tool versions, fonts or timestamps. Progress is unchanged."
            final_log = out / f"{entry.stem}.log"
            log_text = final_log.read_text(encoding="utf-8", errors="replace") if final_log.exists() else ""
            result["diagnostics"] = [line for line in log_text.splitlines()
                                     if re.search(r"^!|Overfull \\[hv]box|Missing character:|(?:LaTeX|Package \S+) Warning:", line)]
            result["diagnostics_scope"] = "Final TeX log: errors, overfull boxes, missing characters and LaTeX/package warnings; not visual inspection."
            if result["diagnostics"]:
                result["result"] = "built_with_warnings"
    result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (out / "build_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def render_text(result):
    print(f"Result: {result['result']}")
    if "completed_count" in result:
        print(f"Completed: {result.get('completed_count')} / {result.get('catalog_total')}; remaining: {result.get('remaining_count')}")
        print(f"Next: {result.get('next_index')} — {result.get('next_title')}")
        print(f"Next source prepared: {result.get('next_source_prepared')}; translation started: {result.get('next_translation_started')}")
        print(f"State: {result['state_source']}")
        print(f"Fixed source commit: {result.get('source_commit')}")
        missing = [r["index"] for r in result["records"] if not (r["entrypoint_present"] and r["pdf_present"])]
        print(f"Missing recorded entrypoint/PDF: {missing or 'none'}")
        print(json.dumps(result["evidence_scope"], ensure_ascii=False))
    elif "compile_ready" in result:
        print(f"Compilation ready: {result['compile_ready']}")
        for name, row in result["commands"].items():
            if row["required_for_rebuild"]:
                print(f"  {name}: {row['path'] or 'MISSING'}")
        for row in result["tex_resources"]:
            print(f"  {row['name']}: {row['resolved_path'] or 'NOT FOUND'}")
        for row in result["broken_tex_filename_databases"]:
            print(f"  Broken TeX database link: {row['path']} -> {row['target']}")
        print("Optional PDF packages are not required for status or verify.")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=DEFAULT_STATE, help="Project-relative state JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "next"):
        sub.add_parser(name).add_argument("--json", action="store_true")
    p = sub.add_parser("doctor")
    p.add_argument("--json", action="store_true")
    p.add_argument("--compile-probe", action="store_true", help="Compile one minimal document under runtime/doctor; never install dependencies")
    p = sub.add_parser("build")
    p.add_argument("paper", type=int, help="Completed paper number, e.g. 18 or 0018")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out", help="Project-relative output under runtime/")
    p.add_argument("--passes", type=int, default=4)
    p.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            result = status(args.state)
        elif args.command == "next":
            result = next_item(args.state)
        elif args.command == "doctor":
            result = doctor(args.compile_probe, args.state)
        else:
            result = build(args.paper, args.state, args.out, args.passes, args.dry_run)
    except (ProjectError, OSError) as exc:
        if args.json:
            print(json.dumps({"result": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        render_text(result)
    return 0 if result["result"] in ("ok", "ready", "planned", "built", "built_with_warnings") else 1


if __name__ == "__main__":
    raise SystemExit(main())
