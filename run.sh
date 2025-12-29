#!/bin/bash
# Wrapper script för GEMMIS CLI
cd "$(dirname "$0")"
python3 -m gemmis "$@"
