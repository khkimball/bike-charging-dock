#!/usr/bin/env bash
# Headless sanity check: load every exported STL in Snapmaker Orca (CLI mode)
# and write an Orca project 3MF per part. Fails if Orca rejects a file.
# The Flatpak has no host filesystem access, so grant this repo for the run.
set -euo pipefail
cd "$(dirname "$0")/.."
APP=io.github.Snapmaker.Snapmaker_Orca
OUT=out/orca
mkdir -p "$OUT"
status=0
for stl in out/*.stl; do
  name=$(basename "$stl" .stl)
  if flatpak run --filesystem="$PWD" "$APP" --export-3mf "$name.3mf" --outputdir "$OUT" "$stl" >/dev/null 2>&1 \
     && grep -q "\"return_code\": 0" "$OUT/result.json"; then
    echo "ok    $name"
  else
    echo "FAIL  $name"; status=1
  fi
done
exit $status
