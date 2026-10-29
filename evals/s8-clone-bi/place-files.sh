#!/usr/bin/env bash
set -eu
SRC="$(dirname "$0")/../../examples/clone-bi-synthetic"
cp -R "$SRC/Alpha.Report" "$SRC/Alpha.SemanticModel" "$SRC/Beta.Report" "$SRC/Beta.SemanticModel" .
