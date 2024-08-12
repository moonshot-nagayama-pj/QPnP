#!/usr/bin/env bash

# Installs dependency for Ubuntu Linux, which is used on Github Actions

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
    errmsg 'There is an error installing the dependencies.'
    exit 1
  fi
}
trap trap_exit EXIT

# Update package list and install shfmt (other dependencies are built-in)
sudo apt-get update
sudo apt-get install shfmt -y
