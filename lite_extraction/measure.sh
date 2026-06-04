#!/usr/bin/env bash
# Append a footprint measurement to sizes.csv. Usage: measure.sh "<phase label>"
set -euo pipefail
cd "$(dirname "$0")/.."
SP=.venv/Lib/site-packages
LABEL="${1:-unlabeled}"

sp_kb=$(du -sk "$SP" 2>/dev/null | cut -f1)
src_kb=$(du -sk python_modules/dagster/dagster 2>/dev/null | cut -f1)
total_kb=$((sp_kb + src_kb))

csv=lite_extraction/sizes.csv
if [ ! -f "$csv" ]; then
  echo "phase,site_packages_kb,dagster_src_kb,total_kb,total_mb" > "$csv"
fi
mb=$(awk "BEGIN{printf \"%.1f\", $total_kb/1024}")
echo "\"$LABEL\",$sp_kb,$src_kb,$total_kb,$mb" >> "$csv"
printf '%-48s site-pkgs=%6sMB  src=%5sMB  TOTAL=%6sMB\n' \
  "$LABEL" \
  "$(awk "BEGIN{printf \"%.1f\", $sp_kb/1024}")" \
  "$(awk "BEGIN{printf \"%.1f\", $src_kb/1024}")" \
  "$mb"
