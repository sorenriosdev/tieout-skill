#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
SRC_PY="$(python3 -c 'import sqlglot,os;print(os.path.dirname(sqlglot.__file__))')"
mkdir -p vendor && cp -R "$SRC_PY" vendor/
