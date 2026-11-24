#!/usr/bin/env python3
"""Use the bundled Chinese TeX resources without changing the system installation.

Only process-local environment variables are changed. Generated format files and
logs belong to runtime/, not to the preserved manuscript trees.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def build_environment(root=ROOT):
    """Return a subprocess environment dict; do not install or write anything."""
    root = Path(root).resolve()
    env = os.environ.copy()
    vendor = root / 'vendor/texmf'
    if not vendor.is_dir():
        return env
    env['TEXMFHOME'] = str(vendor)
    env['TEXMFVAR'] = str(root / 'runtime/texmf-var')
    env['TEXMFCONFIG'] = str(root / 'runtime/texmf-config')
    kpse = shutil.which('kpsewhich', path=env.get('PATH'))
    if kpse:
        result = subprocess.run([kpse, '--var-value=TEXMF'], env=env,
                                capture_output=True, text=True, timeout=20)
        if result.returncode == 0 and result.stdout.strip():
            # !! requires a filename database. Removing it permits ordinary
            # directory lookup when a relocated TeX tree has no valid ls-R.
            env['TEXMF'] = '{' + str(vendor) + ',' + result.stdout.strip().replace('!!', '') + '}'
    return env


def prepare_format(root=ROOT):
    """Generate xelatex.fmt in runtime using installed TeX binaries/packages."""
    root = Path(root).resolve()
    env = build_environment(root)
    work = root / 'runtime/texmf-var'
    work.mkdir(parents=True, exist_ok=True)
    (root / 'runtime/texmf-config').mkdir(parents=True, exist_ok=True)
    attempts = []
    command = ['fmtutil-user', '--byfmt', 'xelatex']
    if shutil.which(command[0]):
        result = subprocess.run(command, cwd=work, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True)
        log = work / 'prepare-xelatex-format.log'
        log.write_text(result.stdout, encoding='utf-8')
        attempts.append({'command': command, 'exit_code': result.returncode,
                         'log': str(log.relative_to(root))})
    probe = subprocess.run(['kpsewhich', '--engine=xetex', 'xelatex.fmt'],
                           env=env, capture_output=True, text=True)
    if probe.returncode != 0:
        # A minimal runtime may retain TeX files but lack generated fmtutil.cnf.
        # Use the distribution's unchanged standard xelatex.ini directly.
        direct_work = work / 'web2c/xetex'
        direct_work.mkdir(parents=True, exist_ok=True)
        command = ['xetex', '-ini', '-etex', '-interaction=nonstopmode',
                   '-halt-on-error', '-jobname=xelatex', '-progname=xelatex',
                   'xelatex.ini']
        result = subprocess.run(command, cwd=direct_work, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True)
        log = work / 'prepare-xelatex-direct.log'
        log.write_text(result.stdout, encoding='utf-8')
        attempts.append({'command': command, 'exit_code': result.returncode,
                         'log': str(log.relative_to(root)),
                         'fallback_hyphenation_used': 'I will try the file hyphen.tex' in result.stdout})
        probe = subprocess.run(['kpsewhich', '--engine=xetex', 'xelatex.fmt'],
                               env=env, capture_output=True, text=True)
    return {'attempts': attempts, 'format_path': probe.stdout.strip(),
            'format_found': probe.returncode == 0,
            'status': 'pass' if probe.returncode == 0 else 'failed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['env', 'prepare'])
    args = parser.parse_args()
    if args.command == 'env':
        env = build_environment(ROOT)
        print(json.dumps({key: env[key] for key in ['TEXMF', 'TEXMFHOME', 'TEXMFVAR', 'TEXMFCONFIG'] if key in env}, ensure_ascii=False, indent=2))
        return 0
    result = prepare_format(ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
