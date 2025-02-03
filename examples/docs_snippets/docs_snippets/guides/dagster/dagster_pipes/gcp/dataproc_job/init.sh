#!/bin/bash

# this is an init action for a Dataproc cluster that installs a PEX file into the cluster's environment
# requires setting the PEX_ENV_FILE_URI cluster metadata key to the URI of the PEX file to install

set -exo pipefail

readonly PEX_ENV_FILE_URI=$(/usr/share/google/get_metadata_value attributes/PEX_ENV_FILE_URI || true)
readonly PEX_FILES_DIR="/pexfiles"
readonly PEX_ENV_DIR="/pexenvs"

function err() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
    exit 1
}

function install_pex_into_venv() {
    local -r pex_name=${PEX_ENV_FILE_URI##*/}
    local -r pex_file="${PEX_FILES_DIR}/${pex_name}"
    local -r pex_venv="${PEX_ENV_DIR}/${pex_name}"

    echo "Installing pex from ${pex_file} into venv ${pex_venv}..."
    gsutil cp "${PEX_ENV_FILE_URI}" "${pex_file}"
    PEX_TOOLS=1 python "${pex_file}" venv --compile "${pex_venv}"
}

function main() {
    if [[ -z "${PEX_ENV_FILE_URI}" ]]; then
        err "ERROR: Must specify PEX_ENV_FILE_URI metadata key"
    fi

    install_pex_into_venv
}

main
