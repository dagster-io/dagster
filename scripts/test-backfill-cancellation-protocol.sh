#!/bin/sh
# Source QA plus real disposable Kind run/step cancellation; all assets are local.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec uv --no-config run --no-project --isolated --python 3.14.6 \
  python "$script_dir/backfill_cancellation/run.py" "$@"
