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

# Update package list and install curl and shellcheck
sudo apt-get update
sudo apt-get install curl shellcheck -y

# Install shfmt
download_dir=$(mktemp -d 'shfmt.XXXXXXXX')
exec_name="shfmt_v3.8.0_linux_amd64"
exec_path="${download_dir}"/"${exec_name}"
sha256_name="sha256sums.txt"
sha256_path="${download_dir}"/"${sha256_name}"
curl --location \
  --output-dir "${download_dir}" \
  --remote-name-all \
  "https://github.com/mvdan/sh/releases/download/v3.8.0/${sha256_name}" \
  "https://github.com/mvdan/sh/releases/download/v3.8.0/${exec_name}"
# Get the first part of the shasum string for the correct file, which is formatted as "<checksum> <filename>"
shasum_str=$(grep "${exec_name}" "${sha256_path}" | cut -d ' ' -f 1)
# Write it back to the file for comparison
stdmsg "${shasum_str}" >"${sha256_path}"
# shellcheck disable=SC2312
sha256sum --check <(stdmsg "$(<"${sha256_path}") ${exec_path}")
mv "${exec_path}" /usr/local/bin/shfmt
chmod +x /usr/local/bin/shfmt
