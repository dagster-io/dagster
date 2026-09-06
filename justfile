# CI-oriented recipes. These are used by Buildkite step definitions and replace
# the equivalent Makefile targets. Unlike make, just propagates signal exit codes
# (e.g. 130 for SIGINT, 143 for SIGTERM) instead of masking them, which allows
# Buildkite's automatic retry to detect infrastructure failures like spot
# instance reclamation.

export COREPACK_ENABLE_DOWNLOAD_PROMPT := "0"

check_ruff:
    ruff check .
    ruff format --check .

install_prettier:
    npm install -g prettier

# NOTE: excludes symlinked md files
check_prettier:
    #!/usr/bin/env bash
    set -euo pipefail
    prettier $(git ls-files \
        'python_modules/*.yml' 'python_modules/*.yaml' 'helm/*.yml' 'helm/*.yaml' \
        '*.md' '.claude/*.md' \
        ':!:docs/*.md' ':!:helm/**/templates/*.yml' ':!:helm/**/templates/*.yaml' \
        ':!:README.md' ':!:GEMINI.md') \
        --check

prettier:
    #!/usr/bin/env bash
    set -euo pipefail
    prettier $(git ls-files \
        'python_modules/*.yml' 'python_modules/*.yaml' 'helm/*.yml' 'helm/*.yaml' \
        '*.md' '.claude/*.md' \
        ':!:docs/*.md' ':!:helm/**/templates/*.yml' ':!:helm/**/templates/*.yaml' \
        ':!:README.md' ':!:GEMINI.md') \
        --write

ty:
    #!/usr/bin/env bash
    set -euo pipefail
    ulimit -Sn 4096
    python scripts/run-ty.py --all

# ty type checker, only on files changed vs origin/master.
quick-ty *args:
    #!/usr/bin/env bash
    set -euo pipefail
    ulimit -Sn 4096
    python scripts/run-ty.py --diff {{ args }}

# Skip typecheck so that this can be used to test if all requirements can successfully be resolved
# in CI independently of typechecking.
rebuild_ty_pins:
    #!/usr/bin/env bash
    set -euo pipefail
    ulimit -Sn 4096
    python scripts/run-ty.py --update-pins --skip-typecheck

rebuild_ui:
    corepack enable
    cd js_modules && yarn install && yarn workspace @dagster-io/app-oss build

generate-graphql:
    uv run --active --no-project python scripts/generate_graphql.py

# ---------------------------------------------------------------------------
# Local development recipes
# ---------------------------------------------------------------------------

ruff:
    ruff check --fix .
    ruff format .

unsafe_ruff:
    ruff check --fix --unsafe-fixes .
    ruff format .

# Rebuild every ty env from scratch, then typecheck.
rebuild_ty:
    #!/usr/bin/env bash
    set -euo pipefail
    ulimit -Sn 4096
    python scripts/run-ty.py --all --rebuild

install_dev_python_modules:
    python scripts/install_dev_python_modules.py -q

install_dev_python_modules_verbose:
    python scripts/install_dev_python_modules.py

install_dev_python_modules_verbose_m1:
    python scripts/install_dev_python_modules.py --include-prebuilt-grpcio-wheel

# Fail if any dagster package is installed non-editably (dagster-hex/-hightouch are external).
sanity_check:
    @echo "Checking for prod installs - if any are listed below reinstall with 'uv pip install -e'"
    @! (uv pip list --exclude-editable | grep -e dagster | grep -v dagster-hex | grep -v dagster-hightouch)

rebuild_ui_with_profiling:
    corepack enable
    cd js_modules && yarn install && yarn build-with-profiling

dev_install: install_dev_python_modules_verbose sanity_check rebuild_ui

dev_install_quiet: install_dev_python_modules sanity_check rebuild_ui

dev_install_m1_grpcio_wheel: install_dev_python_modules_verbose_m1 sanity_check rebuild_ui

graphql_tests:
    pytest python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv

check_manifest:
    check-manifest python_modules/dagster
    check-manifest python_modules/dagster-webserver
    check-manifest python_modules/dagster-graphql
    ls python_modules/libraries | xargs -n 1 -Ipkg check-manifest python_modules/libraries/pkg

format_docs:
    cd docs && yarn format
