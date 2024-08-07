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

# Returns 0 if the environment variable is set to any value including
# null, 1 otherwise.
is_set() {
  [[ -n ${!1+x} ]]
}

# Update package list
apt-get update

# Install wget and shellcheck
apt-get update
apt-get install wget xz-utils -y

# Install shellcheck
wget https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck-v0.10.0.linux.aarch64.tar.xz --output-document /tmp/shellcheck.tar.xz
tar xJf /tmp/shellcheck.tar.xz --directory /tmp
mv /tmp/shellcheck-v0.10.0/shellcheck /usr/local/bin/shellcheck
rm -rf /tmp/shellcheck-v0.10.0 /tmp/shellcheck.tar.xz

# Install shfmt
wget https://github.com/mvdan/sh/releases/download/v3.8.0/shfmt_v3.8.0_linux_amd64 --output-document /usr/local/bin/shfmt
chmod +x /usr/local/bin/shfmt
