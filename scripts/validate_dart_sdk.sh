#!/usr/bin/env bash
# Validates that the repo OpenAPI spec can generate a compatible Dart SDK.
# Usage: ./scripts/validate_dart_sdk.sh [path/to/openapi.json]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATION_DIR="$REPO_ROOT/tools/dart_sdk_validation"
DEFAULT_SPEC="$REPO_ROOT/fluxer_api/src/api/openapi/openapi.json"
SPEC_PATH="${1:-$DEFAULT_SPEC}"

if [[ ! -f "$SPEC_PATH" ]]; then
  echo "ERROR: OpenAPI spec not found: $SPEC_PATH"
  exit 1
fi

echo "=== Step 1/5: Checking prerequisites ==="
command -v dart >/dev/null 2>&1 || { echo "ERROR: dart not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }

echo "=== Step 2/5: Copying and patching OpenAPI spec ==="
cp "$SPEC_PATH" "$VALIDATION_DIR/openapi.json"
python3 "$VALIDATION_DIR/scripts/patch_openapi_spec.py" "$VALIDATION_DIR/openapi.json"

echo "=== Step 3/5: Generating SDK ==="
cd "$VALIDATION_DIR"
find lib/ -mindepth 1 ! -name '.*' ! -name '.gitkeep' -exec rm -rf {} + 2>/dev/null || true
dart pub get
dart run openapi_sdk_gen --file openapi_generator.yaml

echo "=== Step 4/5: Running build_runner ==="
dart run build_runner build --delete-conflicting-outputs

echo "=== Step 5/5: Running dart analyze ==="
dart analyze --no-fatal-warnings

echo "=== Validation successful ==="
echo "OpenAPI spec is compatible with Dart SDK generation"
