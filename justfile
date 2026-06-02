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
    python scripts/run-ty.py --diff {{args}}

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
