#!/bin/bash
# GEMMIS CLI wrapper
cd "$(dirname "$0")"
# Ensure we are using the local python environment where dependencies are installed
exec python3 -m gemmis.cli "$@"
