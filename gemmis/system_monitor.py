"""
System Monitor - Monitor computer health and resources
"""

import subprocess
from datetime import datetime
from pathlib import Path

import psutil


class SystemMonitor:
    """Monitor system resources and health"""

    def __init__(self):
        self.psutil_available = True
        try:
            import psutil
        except ImportError:
            self.psutil_available = False

    def get_cpu_stats(self) -> dict:
        """Get CPU usage statistics"""
        if not self.psutil_available:
            return {}

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            return {
                "usage": cpu_percent,
                "cores": cpu_count,
                "freq_current": cpu_freq.current if cpu_freq else None,
                "freq_max": cpu_freq.max if cpu_freq else None,
            }
        except Exception:
            return {}

    def get_memory_stats(self) -> dict:
        """Get memory (RAM) statistics"""
        if not self.psutil_available:
            return {}

        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "total": mem.total,
                "used": mem.used,
                "available": mem.available,
                "percent": mem.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent,
            }
        except Exception:
            return {}

    def get_disk_stats(self) -> list[dict]:
        """Get disk usage statistics for all partitions"""
        if not self.psutil_available:
            return []

        try:
            disks = []
            partitions = psutil.disk_partitions()

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                        }
                    )
                except PermissionError:
                    continue

            return disks
        except Exception:
            return []

    def get_network_stats(self) -> dict:
        """Get network I/O statistics"""
        if not self.psutil_available:
            return {}

        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            }
        except Exception:
            return {}

    def get_top_processes(self, limit: int = 5, sort_by: str = "cpu") -> list[dict]:
        """Get top processes by CPU or memory usage"""
        if not self.psutil_available:
            return []

        try:
            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent", "memory_info"]
            ):
                try:
                    pinfo = proc.info
                    processes.append(
                        {
                            "pid": pinfo["pid"],
                            "name": pinfo["name"],
                            "cpu_percent": pinfo["cpu_percent"] or 0,
                            "memory_percent": pinfo["memory_percent"] or 0,
                            "memory_mb": (pinfo["memory_info"].rss / 1024 / 1024)
                            if pinfo["memory_info"]
                            else 0,
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort and limit
            sort_key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
            processes.sort(key=lambda x: x[sort_key], reverse=True)
            return processes[:limit]
        except Exception:
            return []

    def get_system_info(self) -> dict:
        """Get general system information"""
        if not self.psutil_available:
            return {}

        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            return {
                "boot_time": boot_time.isoformat(),
                "uptime_days": uptime.days,
                "uptime_hours": uptime.seconds // 3600,
                "uptime_minutes": (uptime.seconds % 3600) // 60,
            }
        except Exception:
            return {}

    def get_system_health(self) -> dict:
        """Get overall system health assessment"""
        health = {
            "status": "healthy",
            "warnings": [],
            "issues": [],
            "recommendations": [],
        }

        # Check CPU
        cpu = self.get_cpu_stats()
        if cpu.get("usage", 0) > 90:
            health["warnings"].append("CPU usage is very high (>90%)")
            health["status"] = "warning"
        elif cpu.get("usage", 0) > 80:
            health["warnings"].append("CPU usage is high (>80%)")

        # Check memory
        mem = self.get_memory_stats()
        if mem.get("percent", 0) > 90:
            health["issues"].append("Memory usage is critical (>90%)")
            health["status"] = "critical"
        elif mem.get("percent", 0) > 80:
            health["warnings"].append("Memory usage is high (>80%)")
            health["status"] = "warning"

        # Check swap
        if mem.get("swap_percent", 0) > 50:
            health["warnings"].append("Swap usage is high - consider adding more RAM")

        # Check disk space
        disks = self.get_disk_stats()
        for disk in disks:
            if disk.get("percent", 0) > 90:
                health["issues"].append(f"Disk {disk['mountpoint']} is almost full (>90%)")
                health["status"] = "critical"
            elif disk.get("percent", 0) > 80:
                health["warnings"].append(f"Disk {disk['mountpoint']} is getting full (>80%)")
                if health["status"] == "healthy":
                    health["status"] = "warning"

        # Recommendations
        if mem.get("percent", 0) > 70:
            health["recommendations"].append("Consider closing unused applications to free memory")

        if cpu.get("usage", 0) > 70:
            health["recommendations"].append("Check for CPU-intensive processes")

        # Check for large files taking up space
        full_disks = [d for d in disks if d.get("percent", 0) > 80]
        if full_disks:
            health["recommendations"].append("Consider cleaning up disk space")

        return health

    def check_updates(self) -> dict:
        """Check for system updates (dnf/apt/pacman)"""
        managers = [
            ("dnf", ["dnf", "check-update", "--quiet"], 100),  # 100 is return code for updates
            ("apt", ["apt", "list", "--upgradable"], 0),
            ("pacman", ["checkupdates"], 0),
        ]

        found_manager = None
        for mgr, cmd, success_code in managers:
            try:
                if subprocess.run(["which", mgr], capture_output=True).returncode == 0:
                    found_manager = (mgr, cmd, success_code)
                    break
            except Exception:
                continue

        if not found_manager:
            return {"available": False, "count": 0, "output": "No supported package manager found"}

        mgr_name, check_cmd, update_code = found_manager

        try:
            # APT needs special handling because it returns 0 even if no updates
            # and prints "Listing..." which we need to filter
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=15)

            output = result.stdout or ""
            count = 0

            if mgr_name == "dnf":
                if result.returncode == 100:  # DNF returns 100 if updates available
                    # Count lines that look like packages
                    lines = [
                        l
                        for l in output.split("\n")
                        if l.strip() and not l.startswith("Last") and not l.startswith("Upgraded")
                    ]
                    count = len(lines)
            elif mgr_name == "apt":
                # First line is usually "Listing...", skip it
                lines = [
                    l
                    for l in output.split("\n")
                    if l.strip() and "/" in l and "Listing..." not in l
                ]
                count = len(lines)
            elif mgr_name == "pacman":
                count = len([l for l in output.split("\n") if l.strip()])

            return {
                "available": count > 0,
                "count": count,
                "output": output[:500] if output else "",
                "manager": mgr_name,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            return {"available": False, "count": 0, "output": str(e)}

    def get_large_files(self, path: str = "/home", limit: int = 10) -> list[dict]:
        """Find large files in a directory"""
        if not self.psutil_available:
            return []

        try:
            large_files = []
            path_obj = Path(path)

            if not path_obj.exists():
                return []

            for item in path_obj.rglob("*"):
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        if size > 100 * 1024 * 1024:  # Files larger than 100MB
                            large_files.append(
                                {
                                    "path": str(item),
                                    "size": size,
                                    "size_mb": size / (1024 * 1024),
                                }
                            )
                except (PermissionError, OSError):
                    continue

            large_files.sort(key=lambda x: x["size"], reverse=True)
            return large_files[:limit]
        except Exception:
            return []


# Global instance
_monitor = None


def get_monitor() -> SystemMonitor:
    """Get or create system monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor
