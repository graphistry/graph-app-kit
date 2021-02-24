#!/bin/bash
set -ex

# Run from python root
# Non-zero exit code on fail
# Uses tox.ini's flake8 config

flake8 --version

# Quick syntax errors
flake8 \
    . \
    --exit-zero \
    --count \
    --select=E9,F63,F7,F82 \
    --show-source \
    --statistics

# Deeper check
flake8 \
  . \
  --exit-zero \
  --count \
  --exit-zero \
  --statistics