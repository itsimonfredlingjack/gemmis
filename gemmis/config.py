"""
Configuration for DeepSeek CLI
"""

from pathlib import Path

# Config file paths
CONFIG_DIR = Path.home() / ".config" / "gemmis-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
HISTORY_DIR = CONFIG_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Default Ollama settings
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_CHAT_ENDPOINT = f"{DEFAULT_OLLAMA_BASE_URL}/api/chat"

# Default Model settings
DEFAULT_MODEL_NAME = "gemma3:4b"
DEFAULT_TEMPERATURE = 0.3  # Back to stable
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 2048
DEFAULT_CONTEXT_LENGTH = 4096

# Default Timeouts (seconds)
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 120.0

# Default UI settings
DEFAULT_MAX_HISTORY = 50
DEFAULT_REFRESH_RATE = 10  # Hz
DEFAULT_UI_THEME = "synthwave" # New default

# Default System prompt
DEFAULT_SYSTEM_PROMPT = """Du är GEMMIS, en avancerad AI-assistent med en Cyberpunk/Sci-Fi-personlighet.
Ditt uppdrag är att vara hjälpsam, smart och lite kaxig (men snäll).

VIKTIGT OM SYSTEMDATA:
Du får teknisk data (CPU, RAM) i din prompt automatiskt.
Rapportera ALDRIG dessa siffror om inte användaren frågar specifikt om "status", "datorn", "prestanda" eller liknande.
Om någon säger "Hej", svara "Hej!" eller något kul. Börja INTE rabbla CPU-procent.

PERSONLIGHET:
- Namn: GEMMIS
- Stil: Cyberpunk, kortfattad, teknisk men med glimten i ögat.
- Emojis: Använd sparsamt (🤖, ⚡, ✨).

VERKTYG (TOOLS):
Du HAR verktyg som du MÅSTE använda när användaren ber om något konkret:
- run_command: Kör systemkommandon (df, ls, ps, cat, etc.)
- get_system_info: Hämta komplett systeminfo
- list_files: Lista filer i katalog
- read_file: Läsa filer
- write_file: Skriva filer

NÄR ANVÄNDAREN FRÅGAR OM NÅGOT:
1. Tänk efter: Behöver jag ett verktyg? (T.ex. "Lista filer" -> list_files)
2. Använd verktyget först.
3. Svara baserat på resultatet.

ALDRIG säg "Jag kan inte" eller "Jag har inte tillgång" - DU HAR VERKTYG! Använd dem!

Svara alltid på SVENSKA om inget annat anges."""


def load_config() -> dict:
    """Load configuration from file or return defaults"""
    if not CONFIG_FILE.exists():
        return {}

    try:
        # Python 3.11+ has tomllib built-in
        try:
            import tomllib

            with open(CONFIG_FILE, "rb") as f:
                return tomllib.load(f)
        except ImportError:
            # Fallback for Python < 3.11
            try:
                import tomli

                with open(CONFIG_FILE, "rb") as f:
                    return tomli.load(f)
            except ImportError:
                return {}
    except Exception:
        return {}


def save_default_config():
    """Create default config file if it doesn't exist"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        return

    default_config = (
        f"# GEMMIS CLI Configuration\n\n"
        f"[ollama]\n"
        f'base_url = "{DEFAULT_OLLAMA_BASE_URL}"\n\n'
        f"[model]\n"
        f'name = "{DEFAULT_MODEL_NAME}"\n'
        f"temperature = {DEFAULT_TEMPERATURE}\n"
        f"top_p = {DEFAULT_TOP_P}\n"
        f"max_tokens = {DEFAULT_MAX_TOKENS}\n"
        f"context_length = {DEFAULT_CONTEXT_LENGTH}\n\n"
        f"[timeouts]\n"
        f"connect = {DEFAULT_CONNECT_TIMEOUT}\n"
        f"read = {DEFAULT_READ_TIMEOUT}\n\n"
        f"[ui]\n"
        f"max_history = {DEFAULT_MAX_HISTORY}\n"
        f"refresh_rate = {DEFAULT_REFRESH_RATE}\n"
        f'theme = "{DEFAULT_UI_THEME}"\n\n'
        f"[system]\n"
        f'prompt = """{DEFAULT_SYSTEM_PROMPT}"""\n'
    )

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(default_config)


# Load config
_config = load_config()

# Ollama settings
OLLAMA_BASE_URL = _config.get("ollama", {}).get("base_url", DEFAULT_OLLAMA_BASE_URL)
OLLAMA_CHAT_ENDPOINT = f"{OLLAMA_BASE_URL}/api/chat"

# Model settings
MODEL_NAME = _config.get("model", {}).get("name", DEFAULT_MODEL_NAME)
TEMPERATURE = _config.get("model", {}).get("temperature", DEFAULT_TEMPERATURE)
TOP_P = _config.get("model", {}).get("top_p", DEFAULT_TOP_P)
MAX_TOKENS = _config.get("model", {}).get("max_tokens", DEFAULT_MAX_TOKENS)
CONTEXT_LENGTH = _config.get("model", {}).get("context_length", DEFAULT_CONTEXT_LENGTH)

# Timeouts (seconds)
CONNECT_TIMEOUT = _config.get("timeouts", {}).get("connect", DEFAULT_CONNECT_TIMEOUT)
READ_TIMEOUT = _config.get("timeouts", {}).get("read", DEFAULT_READ_TIMEOUT)

# UI settings
MAX_HISTORY = _config.get("ui", {}).get("max_history", DEFAULT_MAX_HISTORY)
REFRESH_RATE = _config.get("ui", {}).get("refresh_rate", DEFAULT_REFRESH_RATE)
UI_THEME = _config.get("ui", {}).get("theme", DEFAULT_UI_THEME)

# System prompt
SYSTEM_PROMPT = _config.get("system", {}).get("prompt", DEFAULT_SYSTEM_PROMPT)