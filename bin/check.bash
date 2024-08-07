#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# Print functions
stdmsg() {
  local IFS=' '
  printf '%s\n' "$*"
}

errmsg() {
  stdmsg "$*" 1>&2
}

# Trap exit handler
trap_exit() {
  # It is critical that the first line capture the exit code. Nothing
  # else can come before this. The exit code recorded here comes from
  # the command that caused the script to exit.
  local exit_status="$?"

  if [[ ${exit_status} -ne 0 ]]; then
    errmsg 'Errors are found in one or more files. Please fix them before committing.'
    exit 1
  fi
}
trap trap_exit EXIT

base_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd -P)"
project_dir="${base_dir}"/..

# cd to the directory before running rye
cd "${project_dir}" || exit 1

# Check rye version (and whether it's installed or not)
# stdmsg "Checking if rye is installed..."
# version_string=$(rye --version | head -n 1 | cut -d ' ' -f 2)
# stdmsg "Rye version: ${version_string}"

# Sync with rye
stdmsg "Running rye sync..."
rye sync

# Activate virtual environment
stdmsg "Activating virtual environment..."
source .venv/bin/activate

# Run black check
stdmsg "Checking Python code formatting with black..."
black --check --diff src tests

# Shell check
# Recursively loop through all files and find all files with .sh extension and run shellcheck
stdmsg "Checking Shell scripts with shellcheck..."
find . -type f \( -name "*.sh" -o -name "*.bash" \) -print0 | xargs -0 shellcheck --source-path .:"${HOME}" --enable=all --external-sources

# shfmt
stdmsg "Checking Shell scripts formatting with shfmt..."
shfmt --diff --simplify .

# Run linter
stdmsg "Running Python linter..."
rye lint

# Run unit tests
stdmsg "Running unit tests..."
rye test
