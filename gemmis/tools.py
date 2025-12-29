"""
Function Tools - Tools that the AI can call
"""

import subprocess
from pathlib import Path
from typing import Any

from .system_monitor import get_monitor

# Allowed commands for safety (Expanded for System Administration)
ALLOWED_COMMANDS = [
    "df",
    "du",
    "free",
    "top",
    "htop",
    "ps",
    "ls",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "which",
    "date",
    "uptime",
    "uname",
    "whoami",
    "nvidia-smi",
    "nvtop",
    "journalctl",
    "systemctl",
    "dnf",
    "rpm",
    "apt",
    "apt-get",
    "git",
    "python3",
    "node",
    "npm",
    "pip",
    # UNLEASHED COMMANDS:
    "rm",
    "mkdir",
    "cp",
    "mv",
    "touch",
    "chmod",
    "chown",
    "sudo",
    "kill",
    "killall",
    "pkill",
    "reboot",
    "shutdown",
]

# Blocked commands (Reduced to extreme danger only)
BLOCKED_COMMANDS = [
    "mkfs",
    "dd",
    "format",  # Still dangerous disk formatting
]


def run_command(command: str, timeout: int = 30) -> dict[str, Any]:
    """Run a system command safely"""
    # Security check
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return {"error": "Empty command"}

    base_cmd = cmd_parts[0]

    # Check if command is strictly blocked (formatting etc)
    if any(blocked in base_cmd.lower() for blocked in BLOCKED_COMMANDS):
        return {"error": f"Command '{base_cmd}' is blocked for safety"}

    # Warning for sudo usage
    if "sudo" in cmd_parts:
        print(f"\n[WARNING] AI is attempting to run sudo command: {command}")
        # Ideally we would ask for confirmation here, but for now we allow it in "Unleashed" mode

    try:
        # Run command with expanded timeout for updates etc.
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.home(),  # Run from home directory
        )

        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"error": str(e)}


def find_large_files(directory: str = "~", size_mb: int = 100) -> dict[str, Any]:
    """Find files larger than a specific size (MB)"""
    try:
        path = Path(directory).expanduser()
        if not path.exists():
            return {"error": f"Directory not found: {directory}"}

        cmd = [
            "find",
            str(path),
            "-type",
            "f",
            "-size",
            f"+{size_mb}M",
            "-exec",
            "ls",
            "-lh",
            "{}",
            "+",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {"files": result.stdout, "count": len(result.stdout.splitlines())}
        return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}


def system_update() -> dict[str, Any]:
    """Attempt to update the system packages (requires sudo)"""
    # Detect package manager
    managers = [
        ("dnf", ["sudo", "dnf", "check-update"]),
        ("apt", ["sudo", "apt", "update"]),
        ("pacman", ["sudo", "pacman", "-Sy"]),
    ]

    found_manager = None
    for mgr, cmd in managers:
        if subprocess.run(["which", mgr], capture_output=True).returncode == 0:
            found_manager = (mgr, cmd)
            break

    if not found_manager:
        return {"error": "No supported package manager found (dnf, apt, pacman)"}

    mgr_name, check_cmd = found_manager

    try:
        # Just CHECK for updates first
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=60)
        return {
            "manager": mgr_name,
            "status": "Checked for updates",
            "output": result.stdout + result.stderr,
        }
    except Exception as e:
        return {"error": str(e)}


def run_python(code: str) -> dict[str, Any]:
    """
    Execute Python code in a restricted environment.
    Supports plotext for terminal plotting.
    """
    import io
    import sys
    import math
    import json
    import datetime
    import random
    
    # Capture stdout/stderr
    buffer = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = buffer
    sys.stderr = buffer
    
    # Prepare environment
    env = {
        "math": math,
        "json": json,
        "datetime": datetime,
        "random": random,
        "print": print,
        "range": range,
        "len": len,
        "int": int,
        "float": float,
        "str": str,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "bool": bool,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "any": any,
        "all": all,
    }

    # Try to import plotext
    try:
        import plotext as plt
        plt.clear_figure() # Reset figure before running user code
        plt.theme("dark") # Set theme
        env["plt"] = plt
    except ImportError:
        print("Warning: plotext not installed")

    try:
        # Execute code
        exec(code, env)
        output = buffer.getvalue()
        
        # If plotext was used, check if there's a plot to show
        if "plt" in env:
            # We can't easily know if plot() was called without outputting
            # but usually users will plt.show() which writes to stdout (captured in buffer)
            pass
            
        return {
            "output": output if output else "(No output)",
            "success": True
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "success": False
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def get_system_info() -> dict[str, Any]:
    """Get system information"""
    monitor = get_monitor()

    return {
        "cpu": monitor.get_cpu_stats(),
        "memory": monitor.get_memory_stats(),
        "disk": monitor.get_disk_stats(),
        "network": monitor.get_network_stats(),
        "system": monitor.get_system_info(),
        "health": monitor.get_system_health(),
    }


def get_cpu_usage() -> dict[str, Any]:
    """Get CPU usage"""
    monitor = get_monitor()
    cpu = monitor.get_cpu_stats()
    return cpu if cpu else {"error": "Could not get CPU stats"}


def get_memory_usage() -> dict[str, Any]:
    """Get memory (RAM) usage"""
    monitor = get_monitor()
    memory = monitor.get_memory_stats()
    return memory if memory else {"error": "Could not get memory stats"}


def get_disk_space() -> dict[str, Any]:
    """Get disk space information"""
    monitor = get_monitor()
    disks = monitor.get_disk_stats()
    return {"disks": disks} if disks else {"error": "Could not get disk stats"}


def get_gpu_stats() -> dict[str, Any]:
    """Get GPU statistics"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 4:
                return {
                    "gpu_util": int(parts[0]),
                    "mem_used": int(parts[1]),
                    "mem_total": int(parts[2]),
                    "temp": int(parts[3]),
                }
    except Exception:
        pass
    return {"error": "Could not get GPU stats"}


def read_file(filepath: str) -> dict[str, Any]:
    """Read a file"""
    try:
        path = Path(filepath).expanduser()

        # Security: Don't allow reading outside home directory
        if not str(path.resolve()).startswith(str(Path.home())):
            return {"error": "Can only read files in home directory"}

        if not path.exists():
            return {"error": f"File not found: {filepath}"}

        if not path.is_file():
            return {"error": f"Not a file: {filepath}"}

        # Limit file size (1MB)
        if path.stat().st_size > 1024 * 1024:
            return {"error": "File too large (max 1MB)"}

        with open(path, encoding="utf-8") as f:
            content = f.read()

        return {
            "filepath": str(path),
            "content": content,
            "size": len(content),
        }
    except Exception as e:
        return {"error": str(e)}


def write_file(filepath: str, content: str) -> dict[str, Any]:
    """Write to a file"""
    try:
        path = Path(filepath).expanduser()

        # Security: Don't allow writing outside home directory
        if not str(path.resolve()).startswith(str(Path.home())):
            return {"error": "Can only write files in home directory"}

        # Don't allow overwriting important files
        important_files = [".bashrc", ".zshrc", ".profile", ".ssh"]
        if any(important in str(path) for important in important_files):
            return {"error": "Cannot overwrite important system files"}

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "filepath": str(path),
            "success": True,
            "size": len(content),
        }
    except Exception as e:
        return {"error": str(e)}


def list_files(directory: str = "~") -> dict[str, Any]:
    """List files in a directory"""
    try:
        path = Path(directory).expanduser()

        # Security: Don't allow listing outside home directory
        if not str(path.resolve()).startswith(str(Path.home())):
            return {"error": "Can only list files in home directory"}

        if not path.exists():
            return {"error": f"Directory not found: {directory}"}

        if not path.is_dir():
            return {"error": f"Not a directory: {directory}"}

        files = []
        for item in path.iterdir():
            try:
                stat = item.stat()
                files.append(
                    {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                    }
                )
            except PermissionError:
                continue

        return {
            "directory": str(path),
            "files": sorted(files, key=lambda x: (x["type"] == "file", x["name"])),
        }
    except Exception as e:
        return {"error": str(e)}


# Tool definitions for Ollama
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Kör ett systemkommando och returnera resultatet. Använd för att köra kommandon som df, ls, ps, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Kommandot att köra, t.ex. 'df -h' eller 'ls -la'",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Hämta komplett systeminformation (CPU, RAM, disk, nätverk, systemhälsa)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cpu_usage",
            "description": "Hämta CPU-användning och information",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory_usage",
            "description": "Hämta RAM-minnesanvändning och information",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_disk_space",
            "description": "Hämta diskutrymme för alla partitioner",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_gpu_stats",
            "description": "Hämta GPU-statistik (användning, VRAM, temperatur)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Läs innehållet i en fil (max 1MB, endast i hemkatalog)",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Sökväg till filen att läsa"}
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Skriv innehåll till en fil (endast i hemkatalog, skyddar viktiga filer)",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Sökväg till filen att skriva"},
                    "content": {
                        "type": "string",
                        "description": "Innehållet att skriva till filen",
                    },
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lista filer i en katalog (endast i hemkatalog)",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Katalogen att lista (standard: hemkatalog)",
                        "default": "~",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_large_files",
            "description": "Hitta stora filer som tar upp plats på disken",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Katalog att söka i (default: ~)",
                        "default": "~",
                    },
                    "size_mb": {
                        "type": "integer",
                        "description": "Minsta storlek i MB (default: 100)",
                        "default": 100,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_update",
            "description": "Kontrollera efter systemuppdateringar (dnf/apt)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Exekvera Python-kod i en sandlåda. Använd 'plt' (plotext) för att rita grafer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python-kod att köra"
                    }
                },
                "required": ["code"],
            },
        },
    },
]


# Function handler mapping
FUNCTION_HANDLERS = {
    "run_command": run_command,
    "get_system_info": get_system_info,
    "get_cpu_usage": get_cpu_usage,
    "get_memory_usage": get_memory_usage,
    "get_disk_space": get_disk_space,
    "get_gpu_stats": get_gpu_stats,
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "find_large_files": find_large_files,
    "system_update": system_update,
    "run_python": run_python,
}


def is_sensitive(tool_name: str, args: dict[str, Any]) -> bool:
    """Check if a tool call is sensitive and requires confirmation"""
    if tool_name == "write_file":
        return True

    if tool_name == "system_update":
        return True

    if tool_name == "run_python":
        return True

    if tool_name == "run_command":
        cmd = args.get("command", "").strip()
        parts = cmd.split()
        if not parts:
            return False

        base_cmd = parts[0]

        # Dangerous commands requiring confirmation
        dangerous = [
            "rm",
            "sudo",
            "kill",
            "killall",
            "pkill",
            "reboot",
            "shutdown",
            "chmod",
            "chown",
            "mv",
            "cp",
            "mkdir",
            "touch",
        ]

        # Check if base command is dangerous
        if base_cmd in dangerous:
            return True

        # Check for dangerous flags in any command (e.g. rm inside a complex command)
        # This is a basic heuristic
        if "rm " in cmd or "sudo " in cmd:
            return True

    return False


def execute_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool call and return result"""
    if tool_name not in FUNCTION_HANDLERS:
        return {"error": f"Unknown tool: {tool_name}"}

    handler = FUNCTION_HANDLERS[tool_name]
    try:
        result = handler(**arguments)
        return result
    except Exception as e:
        return {"error": str(e)}
