"""
Function Tools - Tools that the AI can call
"""
from .docker_ops import list_containers, get_container_logs
from .git_ops import get_git_status, git_commit

# Tool definitions for Ollama
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_containers",
            "description": "Lista Docker containers (ID, namn, status, image)",
            "parameters": {
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "Visa även stoppade containers",
                        "default": False
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_container_logs",
            "description": "Hämta loggar från en Docker container",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "ID eller namn på containern"
                    },
                    "tail": {
                        "type": "integer",
                        "description": "Antal rader att hämta (default: 100)",
                        "default": 100
                    }
                },
                "required": ["container_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_git_status",
            "description": "Hämta git status och diff statistik",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Skapa en git commit med alla ändringar (.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Commit-meddelande"
                    }
                },
                "required": ["message"],
            },
        },
    },
]

# Function handler mapping
FUNCTION_HANDLERS = {
    "list_containers": list_containers,
    "get_container_logs": get_container_logs,
    "get_git_status": get_git_status,
    "git_commit": git_commit,
}

def execute_tool_call(tool_name: str, arguments: dict) -> dict:
    """Execute a tool call and return result"""
    if tool_name not in FUNCTION_HANDLERS:
        return {"error": f"Unknown tool: {tool_name}"}
    handler = FUNCTION_HANDLERS[tool_name]
    try:
        result = handler(**arguments)
        return result
    except Exception as e:
        return {"error": str(e)}
