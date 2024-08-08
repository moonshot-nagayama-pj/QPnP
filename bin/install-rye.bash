#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

stdmsg() {
  local IFS=' '
  printf '%s\n' "$*"
}

errmsg() {
  stdmsg "$*" 1>&2
}

trap_exit() {
  # It is critical that the first line capture the exit
  # code. Nothing else can come before this.
  #
  # The exit code recorded here comes from the command that caused
  # the script to exit.
  local exit_status="${?}"

  if [[ ${exit_status} -ne 0 ]]; then
    errmsg 'The script did not complete successfully.'
    errmsg 'The exit code was '"${exit_status}"
  fi
}
trap trap_exit EXIT

# Returns 0 if the environment variable is set to any value including
# null, 1 otherwise.
is_set() {
  [[ -n ${!1+x} ]]
}

download_dir="${1}"

arch=$(uname -m)
if [[ ${arch} == 'aarch64' ]]; then
  gzip_name='rye-aarch64-linux.gz'
elif [[ ${arch} == 'x86_64' ]]; then
  gzip_name='rye-x86_64-linux.gz'
else
  errmsg "Running on unknown or unsupported architecture ${arch}, cannot continue."
  exit 1
fi

sha256_name="${gzip_name}.sha256"

gzip_path="${download_dir}"/"${gzip_name}"
sha256_path="${download_dir}"/"${sha256_name}"
installer_path="${gzip_path%.gz}"

rm -f "${gzip_path}" "${sha256_path}" "${installer_path}"

# wget has better compatibility than curl
wget --directory-prefix="${download_dir}" \
  "https://github.com/astral-sh/rye/releases/latest/download/${sha256_name}" \
  "https://github.com/astral-sh/rye/releases/latest/download/${gzip_name}"

# curl --location \
#   --output-dir "${download_dir}" \
#   --remote-name-all \
#   "https://github.com/astral-sh/rye/releases/latest/download/${sha256_name}" \
#   "https://github.com/astral-sh/rye/releases/latest/download/${gzip_name}"

# shellcheck disable=SC2312
sha256sum --check <(stdmsg "$(<"${sha256_path}") ${gzip_path}")

gunzip "${gzip_path}"
chmod u+x "${installer_path}"
"${installer_path}" self install --yes || true

# Add rye to PATH for Github Actions (persist path)
# shellcheck disable=SC2310
if is_set GITHUB_ENV; then
  source "${HOME}/.rye/env"
  # Write the new path to Github env
  # shellcheck disable=SC2154
  stdmsg "PATH=${PATH}" >>"${GITHUB_ENV}"
fi
