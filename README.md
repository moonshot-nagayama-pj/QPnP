# pnpq
Plug and Play with Quantum!
PnPQ is a python library package for controlling optical devices in quantum networks

## Prerequisites

- [uv](https://docs.astral.sh/uv/).
- shellcheck
- shfmt

## Test and Debug

Since PnPQ is a device driver library, there is no main interface available to run.

Instead, unit tests and hardware tests are available, and can be executed with: `pytest` and `pytest hardware_tests`.

## Making Contributions

Before you commit, ensure that `check.bash` does not output any error. This script checks for formatting errors as well as semantics in Python and shell scripts.

### Formatting

For Python, Black will be used as the standard formatter for this repository. It is part of the recommended plugins, and configured as the default formatter in VSCode.

In VSCode, simply run `>Format Document` in the top menu bar with the Python file opened.
