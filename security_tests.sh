#!/usr/bin/env bash
# Deterministic mocked regressions. No live provider calls or API keys required.
# These tests do not establish resistance against real model jailbreaks.
set -euo pipefail
cd "$(dirname "$0")"
TEST_PYTHON="${TEST_PYTHON:-.venv/bin/python}"
"$TEST_PYTHON" -m unittest discover -s tests -p 'test_chat.py' -v
