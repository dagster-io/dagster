#!/usr/bin/env bash
# Measure the installed footprint of the lightweight Dagster venv.
# Usage: compact_tools/measure.sh [label]
set -euo pipefail

LABEL="${1:-current}"
SP=$(.venv/bin/python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")

echo "=================================================================="
echo "FOOTPRINT MEASUREMENT: ${LABEL}"
echo "site-packages: ${SP}"
echo "=================================================================="
echo "--- total site-packages ---"
du -sh "${SP}"
echo "--- top entries ---"
du -sh "${SP}"/* 2>/dev/null | sort -rh | head -30
echo "=================================================================="
