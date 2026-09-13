#!/usr/bin/env bash
set -euo pipefail

GATE="${1:?Usage: ./scripts/run_gate.sh <gate> [pytest args...]}"
shift || true

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="$ROOT/evidence/v0.6/$GATE"

mkdir -p "$EVIDENCE_DIR"

cd "$ROOT"

COMMIT="$(git rev-parse HEAD)"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
    echo "ECDAT Evidence Record"
    echo "======================"
    echo "Gate:       $GATE"
    echo "Commit:     $COMMIT"
    echo "Timestamp:  $TIMESTAMP"
    echo "Python:     $(python --version 2>&1)"
    echo "Pytest:     $(pytest --version 2>&1)"
    echo "Graphviz:   $(dot -V 2>&1)"
    echo
    echo "Git status:"
    git status --short
} > "$EVIDENCE_DIR/environment.txt"

TEST_EXIT=0

PYTHONPATH=. pytest -q \
    --junit-xml="$EVIDENCE_DIR/junit.xml" \
    "$@" \
    2>&1 | tee "$EVIDENCE_DIR/result.txt" || TEST_EXIT=$?

{
    echo "Gate: $GATE"
    echo "Commit: $COMMIT"
    echo "Exit code: $TEST_EXIT"
    echo "Completed: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
} >> "$EVIDENCE_DIR/result.txt"

if [[ "$TEST_EXIT" -ne 0 ]]; then
    echo
    echo "✗ $GATE FAILED"
    echo "Evidence: $EVIDENCE_DIR"
    exit "$TEST_EXIT"
fi

echo
echo "✓ $GATE PASSED"
echo "Evidence: $EVIDENCE_DIR"
