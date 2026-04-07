#!/usr/bin/env bash

set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
base_venv_dir="${root_dir}/.venv"

locations=(
  "harbor_outfitters catalog_coach_runtime"
  "summit_financial risk_reviewer_runtime"
  "beacon_hq briefing_writer_runtime"
)

for location_spec in "${locations[@]}"; do
  read -r location_name runtime_package <<<"${location_spec}"
  env_dir="${root_dir}/.code_locations/${location_name}/.venv"

  rm -rf "${env_dir}"
  mkdir -p "$(dirname "${env_dir}")"
  cp -a "${base_venv_dir}" "${env_dir}"
  for script_name in dg dagster; do
    script_path="${env_dir}/bin/${script_name}"
    if [[ -f "${script_path}" ]]; then
      perl -0pi -e "s|^#!.*python\\n|#!${env_dir}/bin/python\\n|" "${script_path}"
    fi
  done
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
    "${env_dir}/bin/python" -m pip install --quiet --no-deps --editable \
    "${root_dir}/vendor/${runtime_package}"
done
