#!/usr/bin/env python3
"""
Test script to verify ANSI escape code rendering fix.
This reproduces the minimal case mentioned in the bug report.
"""

import sys
import os
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from prompt_toolkit.patch_stdout import patch_stdout

# Detect terminal capabilities
is_tty = sys.stdout.isatty()
encoding = sys.stdout.encoding or "utf-8"

# Check if terminal supports colors
force_terminal = None
if is_tty:
    term = os.environ.get("TERM", "")
    colorterm = os.environ.get("COLORTERM", "")
    
    if term and term.lower() != "dumb":
        force_terminal = True
    elif colorterm:
        force_terminal = True

# Create console with proper configuration
console = Console(
    force_terminal=force_terminal,
    file=sys.stdout,
    width=None,
    height=None,
    legacy_windows=False,
)

print(f"Terminal: {os.environ.get('TERM', 'unknown')}")
print(f"COLORTERM: {os.environ.get('COLORTERM', 'not set')}")
print(f"TTY: {is_tty}, Encoding: {encoding}, Force terminal: {force_terminal}")
print("\nTesting ANSI escape code rendering...\n")

# Ensure stdout is in the right state
sys.stdout.flush()
sys.stderr.flush()

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

# Test with patch_stdout and Live (the problematic combination)
try:
    with patch_stdout(raw=True):
        with Live(
            Panel("Test ANSI codes - if you see escape sequences as text, the fix didn't work"),
            console=console,
            screen=False,  # Don't use alternate screen for this test
            refresh_per_second=4,
            redirect_stderr=False,
            transient=False,
        ) as live:
            import time
            time.sleep(1)
            live.update(Panel("[bold green]✓[/] ANSI codes working correctly!"))
            time.sleep(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete. Check if ANSI codes were rendered correctly.")
