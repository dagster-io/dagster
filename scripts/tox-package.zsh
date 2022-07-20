# Run a tox test environment for a dagster package.
#
# USAGE:
#   tox-package.zsh PACKAGE TESTENV TESTENV_ARGS...
#
# Globals:
#   DAGSTER_GIT_REPO_DIR: Root directory for dagster repo.
#   DAGSTER_INTERNAL_GIT_REPO_DIR (optional): Root directory for internal dagster repo.
# Arguments:
#   PACKAGE: package identifier, can take three equivalent forms:
#     - repo-relative path: `python_modules/libraries/dagster-snowflake`
#     - basename: `dagster-snowflake`
#     - basename without "dagster-": `snowflake`
#   TESTENV: tox testenv to run
#   TESTENV_ARGS...: args to pass to tox command

if [[ -z $DAGSTER_GIT_REPO_DIR ]]; then
  echo "DAGSTER_GIT_REPO_DIR must be set"
  return 1
fi

# get any tox options-- anything from the start of argv starting with "-"
typeset -a tox_options
while [[ "$1" = -* ]]; do
  tox_options+=($1)
  shift
done

local package="$1"
local testenv="$2"
shift 2
local testenv_args=($@)

# discover and index all packages; "package" here means "directory containing a tox.ini"

typeset -A package_path_map

index_package() {
  # take basename and remove leading "dagster-" if it exists
  local rel_path=$1
  local repo_root=$2
  local abs_path="${repo_root}/${rel_path}"
  local name=$(basename $rel_path)
  local no_dagster_name=${name##dagster-}
  package_path_map[$1]="$abs_path"
  package_path_map[$name]="$abs_path"
  package_path_map[$no_dagster_name]="$abs_path"
}

add_repo_packages() {
  local repo_root="$1"
  pushd $repo_root >/dev/null
  for p in `git ls-files '*/tox.ini'`; do
    index_package "${p:h}" "$repo_root"
  done
  popd >/dev/null
}

add_repo_packages $DAGSTER_GIT_REPO_DIR
if [[ -e "$DAGSTER_INTERNAL_GIT_REPO_DIR" ]]; then
  add_repo_packages $DAGSTER_INTERNAL_GIT_REPO_DIR
fi

local package_path=${package_path_map[$package]}
if [[ -z $package_path ]]; then
  echo "Name $package does not match a known package."
  exit 1
fi

pushd $package_path >/dev/null
# Internal toxfiles expect $DAGSTER_GIT_REPO_DIR to be set
DAGSTER_GIT_REPO_DIR=$DAGSTER_GIT_REPO_DIR tox "${tox_options[@]}" -e $testenv -- "${testenv_args[@]}"
popd >/dev/null
