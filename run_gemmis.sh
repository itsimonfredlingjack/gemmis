#!/bin/bash
# GEMMIS CLI wrapper
cd "$(dirname "$0")"
exec textual run gemmis/app.py "$@"
