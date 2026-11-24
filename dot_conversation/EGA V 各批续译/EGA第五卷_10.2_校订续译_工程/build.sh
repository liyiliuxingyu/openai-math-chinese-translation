#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ -f /workspace/shared/tex-env.sh ]; then source /workspace/shared/tex-env.sh; fi
for i in 1 2; do xelatex -interaction=nonstopmode -halt-on-error "EGA第五卷_10.2_校订续译.tex"; done
