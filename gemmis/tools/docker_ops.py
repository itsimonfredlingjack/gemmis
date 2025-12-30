"""
Docker Operations - Tools for managing Docker containers
"""

import docker
from typing import Any

def get_docker_client():
    try:
        return docker.from_env()
    except Exception:
        return None

def list_containers(all: bool = False) -> dict[str, Any]:
    """List Docker containers"""
    client = get_docker_client()
    if not client:
        return {"error": "Could not connect to Docker daemon. Is it running?"}

    try:
        containers = client.containers.list(all=all)
        result = []
        for c in containers:
            result.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.id,
                "ports": c.ports
            })
        return {"containers": result, "count": len(result)}
    except Exception as e:
        return {"error": str(e)}

def get_container_logs(container_id: str, tail: int = 100) -> dict[str, Any]:
    """Get logs from a container"""
    client = get_docker_client()
    if not client:
        return {"error": "Could not connect to Docker daemon"}

    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=tail).decode('utf-8')
        return {"container": container.name, "logs": logs}
    except Exception as e:
        return {"error": str(e)}
