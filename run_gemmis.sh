#!/bin/bash
# GEMMIS CLI wrapper
cd "$(dirname "$0")"
exec python3 -m gemmis "$@"
