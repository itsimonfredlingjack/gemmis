"""
Git Operations - Tools for Git integration
"""

import subprocess
import os
from typing import Any

def get_git_status() -> dict[str, Any]:
    """Get git status and diff"""
    try:
        # Check if we are in a git repo
        if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode != 0:
            return {"error": "Not a git repository"}

        status = subprocess.run(["git", "status"], capture_output=True, text=True).stdout
        diff_stat = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True).stdout
<<<<<<< HEAD

=======

>>>>>>> origin/main
        return {
            "status": status,
            "diff_stat": diff_stat
        }
    except Exception as e:
        return {"error": str(e)}

def git_commit(message: str) -> dict[str, Any]:
    """Commit changes with a message"""
    try:
        # Check if we are in a git repo
        if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode != 0:
            return {"error": "Not a git repository"}

        # Stage all changes (simplified flow for AI)
        subprocess.run(["git", "add", "."], check=True)
<<<<<<< HEAD

        # Commit
        result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)

=======

        # Commit
        result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)

>>>>>>> origin/main
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}
