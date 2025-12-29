"""
GEMMIS CLI - Command Processing
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import CONFIG_FILE, HISTORY_DIR
from .ollama_client import OllamaClient
from .state import AppState
from .system_monitor import SystemMonitor
from .ui.theme import get_current_theme
from .ui.dashboard import Dashboard
from .audio import get_audio


def save_history(messages: list[dict], filename: str | None = None) -> str:
    """Save chat history to file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_{timestamp}.json"

    filepath = HISTORY_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    return str(filepath)


def load_history(filename: str) -> list[dict] | None:
    """Load chat history from file"""
    filepath = HISTORY_DIR / filename
    if not filepath.exists():
        return None

    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_history_files() -> list[str]:
    """List all saved history files"""
    if not HISTORY_DIR.exists():
        return []

    files = sorted(HISTORY_DIR.glob("chat_*.json"), reverse=True)
    return [f.name for f in files[:10]]  # Last 10 files


def show_help(console: Console):
    """Show help message with theme-aware styling."""
    Colors = get_current_theme()

    help_text = Text()
    help_text.append("COMMAND PROTOCOLS\n\n", style=f"bold {Colors.PRIMARY}")

    commands = [
        # Chat commands
        ("/help", "Display this manual", "INFO"),
        ("/clear", "Wipe terminal buffer", "WIPE"),
        ("/save [name]", "Backup current session", "SAVE"),
        ("/load <name>", "Restore previous session", "LOAD"),
        ("/list", "Index saved sessions", "LIST"),
        ("/export [md|txt]", "Export chat to file", "EXPT"),
        # Memory commands
        ("/sessions", "List all memory sessions", "MEM"),
        ("/session new [name]", "Create new memory session", "NEW"),
        ("/session load <id>", "Load memory session by ID", "LOAD"),
        ("/session search <query>", "Search memory semantically", "SRCH"),
        # System commands
        ("/browse [path]", "Browse directory files", "DIR"),
        ("/tokens", "Show context token usage", "TOK"),
        ("/system", "Hardware diagnostics", "DIAG"),
        ("/health", "System integrity check", "SCAN"),
        ("/top [N]", "Show top N processes", "PROC"),
        # Settings
        ("/theme [name]", "Change visual theme", "THM"),
        ("/persona [name]", "Switch AI personality", "PRS"),
        ("/model", "Query neural net info", "META"),
        ("/config", "Locate config file", "CONF"),
        # Exit
        ("/quit", "Terminate connection", "EXIT"),
    ]

    for cmd, desc, icon in commands:
        help_text.append(f"  [{icon}] ", style=Colors.SECONDARY)
        help_text.append(f"{cmd:<15}", style=f"bold {Colors.PRIMARY}")
        help_text.append(f" :: {desc}\n", style=Colors.TEXT_SECONDARY)

    help_text.append("\n", style=Colors.DIM)
    help_text.append("OPTIMIZATION TIPS\n\n", style=f"bold {Colors.WARNING}")
    help_text.append(
        "  > Use precise prompts for optimal generation\n", style=Colors.TEXT_SECONDARY
    )
    help_text.append(
        "  > First response latency is expected (cold boot)\n", style=Colors.TEXT_SECONDARY
    )

    console.print(
        Panel(
            help_text,
            title=f"[{Colors.PRIMARY}] SYSTEM MANUAL [/]",
            border_style=Colors.PRIMARY,
            style=f"on {Colors.BG_DARK}",
            box=box.HEAVY,
            padding=(1, 2),
        )
    )


async def handle_command(
    cmd: str,
    arg: str | None,
    state: AppState,
    console: Console,
    client: OllamaClient,
    monitor: SystemMonitor,
) -> bool:
    """
    Handle a user command.
    Returns True if the loop should continue, False if it should exit.
    """
    Colors = get_current_theme()

    if cmd in ("/quit", "/exit", "/q"):
        return False

    elif cmd == "/clear":
        state.messages = []
        # Also clear memory session if using memory system
        if state.use_memory and state.session_manager and state.current_session_id:
            try:
                # Create a new session to effectively clear
                new_id = await state.session_manager.create_session(
                    f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                state.current_session_id = new_id
            except Exception:
                pass  # Silently fail if memory system has issues
        console.print(f"[{Colors.SUCCESS}] BUFFER CLEARED[/]")
        await asyncio.sleep(0.5)

    elif cmd == "/help" or cmd == "/commands":
        show_help(console)
        console.input(f"[{Colors.DIM}]Press Enter to continue...[/]")

    elif cmd == "/save":
        if state.messages:
            filename = save_history(state.messages, arg)
            console.print(
                f"[{Colors.SUCCESS}] SESSION SAVED :: [/] [{Colors.PRIMARY}]{filename}[/]"
            )
        else:
            console.print(f"[{Colors.WARNING}] ERROR: NULL BUFFER[/]")
        await asyncio.sleep(1)

    elif cmd == "/load":
        if not arg:
            console.print(f"[{Colors.WARNING}] USAGE: /load <filename>[/]")
            await asyncio.sleep(1)
            return True

        loaded = load_history(arg)
        if loaded:
            state.messages = loaded
            console.print(f"[{Colors.SUCCESS}] SESSION RESTORED :: [/] [{Colors.PRIMARY}]{arg}[/]")
        else:
            console.print(f"[{Colors.ERROR}] ERROR: FILE NOT FOUND[/]")
        await asyncio.sleep(1)

    elif cmd == "/list":
        files = list_history_files()
        if files:
            console.print(f"[{Colors.PRIMARY}] ARCHIVED SESSIONS:[/]")
            for f in files:
                console.print(f"  [{Colors.SECONDARY}]>[/] [{Colors.TEXT_PRIMARY}]{f}[/]")
        else:
            console.print(f"[{Colors.DIM}]NO ARCHIVES FOUND[/]")
        await asyncio.sleep(1.5)

    elif cmd == "/model":
        model_info = await client.get_model_info()
        console.print(f"[{Colors.PRIMARY}] NEURAL NET :: [/] [{Colors.ACCENT}]{client.model}[/]")
        if model_info:
            size = model_info.get("size", 0) / 1e9
            console.print(f"[{Colors.DIM}]SIZE: {size:.2f} GB[/]")
        await asyncio.sleep(1)

    elif cmd == "/config":
        console.print(f"[{Colors.PRIMARY}] CONFIG PATH :: [/] [{Colors.ACCENT}]{CONFIG_FILE}[/]")
        await asyncio.sleep(1)

    elif cmd == "/system":
        # Show detailed system info
        cpu = monitor.get_cpu_stats()
        memory = monitor.get_memory_stats()
        disk = monitor.get_disk_stats()
        # sys_info = monitor.get_system_info() # Unused

        console.print(f"\n[{Colors.PRIMARY}] HARDWARE DIAGNOSTICS [/]\n")

        if cpu:
            console.print(
                f"[{Colors.DIM}]CPU LOAD:[/] [{Colors.ACCENT}]{cpu.get('usage', 0):.1f}%[/] "
                f"({cpu.get('cores', 0)} CORES)"
            )

        if memory:
            mem_used_gb = memory.get("used", 0) / (1024**3)
            mem_total_gb = memory.get("total", 0) / (1024**3)
            console.print(
                f"[{Colors.DIM}]RAM USAGE:[/] [{Colors.ACCENT}]{memory.get('percent', 0):.1f}%[/] "
                f"({mem_used_gb:.1f}/{mem_total_gb:.1f} GB)"
            )

        if disk:
            console.print(f"\n[{Colors.DIM}]STORAGE BANKS:[/]")
            for d in disk[:3]:
                console.print(
                    f"  [{Colors.PRIMARY}]{d['mountpoint']}[/]: "
                    f"[{Colors.ACCENT}]{d.get('percent', 0):.1f}%[/]"
                )

        await asyncio.sleep(2)

    elif cmd == "/health":
        # Show system health check
        health = monitor.get_system_health()

        status_icons = {"healthy": "✓", "warning": "⚠", "critical": "✗"}
        status_colors = {
            "healthy": Colors.SUCCESS,
            "warning": Colors.WARNING,
            "critical": Colors.ERROR,
        }

        icon = status_icons.get(health["status"], "?")
        color = status_colors.get(health["status"], Colors.DIM)

        console.print(f"\n[{color}]{icon} SYSTEM INTEGRITY: {health['status'].upper()}[/]\n")

        if health["warnings"]:
            console.print(f"[{Colors.WARNING}]⚠ WARNINGS DETECTED:[/]")
            for w in health["warnings"]:
                console.print(f"  [{Colors.DIM}]>[/] {w}")

        if health["issues"]:
            console.print(f"\n[{Colors.ERROR}]✗ CRITICAL FAILURES:[/]")
            for i in health["issues"]:
                console.print(f"  [{Colors.DIM}]>[/] {i}")

        if health["recommendations"]:
            console.print(f"\n[{Colors.SECONDARY}]💡 RECOMMENDATIONS:[/]")
            for r in health["recommendations"]:
                console.print(f"  [{Colors.DIM}]>[/] {r}")

        if not health["warnings"] and not health["issues"]:
            console.print(f"[{Colors.SUCCESS}]✓ ALL SYSTEMS NOMINAL[/]")

        await asyncio.sleep(2)

    elif cmd == "/export":
        # Export chat to markdown or text
        if not state.messages:
            console.print(f"[{Colors.WARNING}] ERROR: NULL BUFFER[/]")
            await asyncio.sleep(1)
            return True

        export_format = arg.lower() if arg else "markdown"
        if export_format not in ("markdown", "md", "txt", "text"):
            export_format = "markdown"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if export_format in ("markdown", "md"):
            filename = f"chat_{timestamp}.md"
            content = "# Chat Export\n\n"
            for msg in state.messages:
                role = msg.get("role", "unknown")
                text = msg.get("content", "")
                if role == "user":
                    content += f"## User\n\n{text}\n\n"
                elif role == "assistant":
                    content += f"## Assistant\n\n{text}\n\n"
        else:
            filename = f"chat_{timestamp}.txt"
            content = "Chat Export\n" + "=" * 50 + "\n\n"
            for msg in state.messages:
                role = msg.get("role", "unknown")
                text = msg.get("content", "")
                if role == "user":
                    content += f"USER: {text}\n\n"
                elif role == "assistant":
                    content += f"ASSISTANT: {text}\n\n"

        filepath = HISTORY_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        console.print(f"[{Colors.SUCCESS}] EXPORTED :: [/] [{Colors.PRIMARY}]{filename}[/]")
        await asyncio.sleep(1)

    elif cmd == "/top":
        # Show top processes
        limit = int(arg) if arg and arg.isdigit() else 5
        processes = monitor.get_top_processes(limit=limit, sort_by="cpu")

        console.print(f"\n[{Colors.PRIMARY}] TOP PROCESSES (CPU)[/]\n")
        if processes:
            for i, proc in enumerate(processes, 1):
                console.print(
                    f"  [{Colors.DIM}]{i}.[/] [{Colors.ACCENT}]{proc['name']:<20}[/] "
                    f"CPU: [{Colors.PRIMARY}]{proc['cpu_percent']:.1f}%[/] "
                    f"RAM: [{Colors.SECONDARY}]{proc['memory_mb']:.0f}MB[/]"
                )
        else:
            console.print(f"[{Colors.DIM}]No process data available[/]")

        await asyncio.sleep(2)

    elif cmd == "/updates":
        # Check for system updates
        console.print(f"\n[{Colors.DIM}]Checking for updates...[/]")
        updates = monitor.check_updates()

        if updates.get("available"):
            console.print(f"[{Colors.WARNING}]⚠ {updates['count']} UPDATES AVAILABLE[/]")
            if updates.get("output"):
                console.print(f"[{Colors.DIM}]{updates['output'][:200]}...[/]")
        else:
            console.print(f"[{Colors.SUCCESS}]✓ SYSTEM UP TO DATE[/]")

        await asyncio.sleep(2)

    elif cmd == "/theme":
        # Theme selection/preview
        from .ui.theme import THEMES

        if arg and arg.lower() in THEMES:
            # Preview/set theme
            from .ui.theme import set_theme

            try:
                new_theme = set_theme(arg.lower())
                console.print(f"[{Colors.SUCCESS}]Theme changed to: {new_theme.name}[/]")
                console.print(f"[{Colors.DIM}]Restart for full effect[/]")
            except ValueError as e:
                console.print(f"[{Colors.ERROR}]Error: {e}[/]")
        else:
            # List themes
            console.print(f"\n[{Colors.PRIMARY}] AVAILABLE THEMES [/]\n")
            for name, theme in THEMES.items():
                if name != "aurora":  # Skip legacy
                    marker = ">" if name == "nord" else " "
                    console.print(
                        f"  [{Colors.SECONDARY}]{marker}[/] [{Colors.PRIMARY}]{name:<12}[/] "
                        f"[{Colors.DIM}]{theme.description}[/]"
                    )
            console.print(f"\n[{Colors.DIM}]Usage: /theme <name>[/]")
        await asyncio.sleep(1.5)

    elif cmd == "/persona":
        # Persona selection
        from .personas import PERSONAS, get_persona_description, get_persona_prompt

        if arg and arg.lower() in PERSONAS:
            state.system_prompt = get_persona_prompt(arg.lower())
            desc = get_persona_description(arg.lower())
            console.print(f"[{Colors.SUCCESS}]Persona changed to: {arg.lower()}[/]")
            console.print(f"[{Colors.DIM}]{desc}[/]")
        else:
            console.print(f"\n[{Colors.PRIMARY}] AVAILABLE PERSONAS [/]\n")
            for name in PERSONAS:
                desc = get_persona_description(name)
                marker = ">" if name == "default" else " "
                console.print(
                    f"  [{Colors.SECONDARY}]{marker}[/] [{Colors.PRIMARY}]{name:<12}[/] "
                    f"[{Colors.DIM}]{desc}[/]"
                )
            console.print(f"\n[{Colors.DIM}]Usage: /persona <name>[/]")
        await asyncio.sleep(1.5)

    elif cmd == "/browse":
        # Browse files in current or specified directory

        target_dir = Path(arg) if arg else Path.cwd()
        if not target_dir.exists():
            console.print(f"[{Colors.ERROR}]Directory not found: {target_dir}[/]")
            await asyncio.sleep(1)
            return True

        console.print(f"\n[{Colors.PRIMARY}] DIRECTORY: {target_dir} [/]\n")

        try:
            items = sorted(target_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items[:20]:  # Limit to 20 items
                if item.is_dir():
                    icon = "📁"
                    style = Colors.PRIMARY
                elif item.suffix in (".py", ".js", ".ts", ".rs", ".go"):
                    icon = "📄"
                    style = Colors.SECONDARY
                elif item.suffix in (".md", ".txt", ".rst"):
                    icon = "📝"
                    style = Colors.ACCENT
                else:
                    icon = "📄"
                    style = Colors.DIM

                size = ""
                if item.is_file():
                    size_bytes = item.stat().st_size
                    if size_bytes > 1024 * 1024:
                        size = f"[{Colors.DIM}]{size_bytes / (1024 * 1024):.1f}MB[/]"
                    elif size_bytes > 1024:
                        size = f"[{Colors.DIM}]{size_bytes / 1024:.1f}KB[/]"
                    else:
                        size = f"[{Colors.DIM}]{size_bytes}B[/]"

                console.print(f"  {icon} [{style}]{item.name:<30}[/] {size}")

            if len(list(target_dir.iterdir())) > 20:
                console.print(f"\n  [{Colors.DIM}]... and more[/]")
        except PermissionError:
            console.print(f"[{Colors.ERROR}]Permission denied[/]")

        await asyncio.sleep(2)

    elif cmd == "/sessions":
        # List all memory sessions
        if not state.use_memory or not state.session_manager:
            console.print(f"[{Colors.WARNING}]Memory system not available[/]")
            await asyncio.sleep(1)
            return True
        
        try:
            sessions = await state.session_manager.store.list_sessions()
            if sessions:
                console.print(f"\n[{Colors.PRIMARY}] MEMORY SESSIONS [/]\n")
                for sess in sessions[:10]:  # Show last 10
                    session_id = sess.get("session_id", "")[:8]
                    name = sess.get("name", "Unnamed")
                    created = sess.get("created_at", "")[:10] if sess.get("created_at") else "Unknown"
                    console.print(
                        f"  [{Colors.SECONDARY}]{session_id}[/] "
                        f"[{Colors.PRIMARY}]{name:<30}[/] "
                        f"[{Colors.DIM}]{created}[/]"
                    )
                    if session_id == state.current_session_id[:8]:
                        console.print(f"    [{Colors.SUCCESS}]← CURRENT[/]")
            else:
                console.print(f"[{Colors.DIM}]No sessions found[/]")
        except Exception as e:
            console.print(f"[{Colors.ERROR}]Error: {e}[/]")
        
        await asyncio.sleep(1.5)

    elif cmd == "/dashboard":
        # Launch TUI Dashboard
        dashboard = Dashboard(console, state)
        try:
            await dashboard.run()
        except KeyboardInterrupt:
            pass # Return to chat
        console.clear()
        
    elif cmd == "/speak":
        # Text-to-Speech the last assistant message
        if not state.messages:
             console.print(f"[{Colors.WARNING}]No messages to speak[/]")
        else:
            last_msg = state.messages[-1]
            if last_msg.get("role") == "assistant" and last_msg.get("content"):
                console.print(f"[{Colors.SECONDARY}]🔊 Speaking...[/]")
                await get_audio().speak(last_msg["content"][:500]) # Limit to 500 chars
            else:
                console.print(f"[{Colors.WARNING}]Last message was not from assistant[/]")

    elif cmd == "/testaudio":
        # Test sound effects
        audio = get_audio()
        if not audio.enabled:
             console.print(f"[{Colors.ERROR}]Audio engine disabled (pygame init failed)[/]")
        else:
             console.print(f"[{Colors.PRIMARY}]Testing Audio Channels...[/]")
             sounds = ["startup", "token", "success", "error", "tool"]
             for s in sounds:
                 console.print(f"  Playing: {s}")
                 audio.play(s)
                 await asyncio.sleep(0.5)

    elif cmd == "/session":
        # Handle session subcommands
        if not arg:
            console.print(f"[{Colors.WARNING}]Usage: /session <new|load|search> [args][/]")
            await asyncio.sleep(1)
            return True
        
        if not state.use_memory or not state.session_manager:
            console.print(f"[{Colors.WARNING}]Memory system not available[/]")
            await asyncio.sleep(1)
            return True
        
        parts = arg.split(maxsplit=1)
        subcmd = parts[0].lower()
        subarg = parts[1] if len(parts) > 1 else None
        
        if subcmd == "new":
            # Create new session
            session_name = subarg or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            try:
                new_id = await state.session_manager.create_session(session_name)
                state.current_session_id = new_id
                state.messages = []  # Clear current messages
                console.print(f"[{Colors.SUCCESS}]New session created: {new_id[:8]}[/]")
                console.print(f"[{Colors.DIM}]Name: {session_name}[/]")
            except Exception as e:
                console.print(f"[{Colors.ERROR}]Error: {e}[/]")
        
        elif subcmd == "load":
            # Load existing session
            if not subarg:
                console.print(f"[{Colors.WARNING}]Usage: /session load <session_id>[/]")
                await asyncio.sleep(1)
                return True
            
            try:
                # Try to find session by ID (full or partial)
                sessions = await state.session_manager.store.list_sessions()
                matching = [s for s in sessions if s.get("session_id", "").startswith(subarg)]
                
                if not matching:
                    console.print(f"[{Colors.ERROR}]Session not found: {subarg}[/]")
                    await asyncio.sleep(1)
                    return True
                
                session_id = matching[0]["session_id"]
                state.current_session_id = session_id
                
                # Load messages from session
                context = await state.session_manager.get_context()
                state.messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in context
                    if msg.role != "system"
                ]
                
                console.print(f"[{Colors.SUCCESS}]Session loaded: {session_id[:8]}[/]")
                console.print(f"[{Colors.DIM}]Messages: {len(state.messages)}[/]")
            except Exception as e:
                console.print(f"[{Colors.ERROR}]Error: {e}[/]")
        
        elif subcmd == "search":
            # Semantic search in memory
            if not subarg:
                console.print(f"[{Colors.WARNING}]Usage: /session search <query>[/]")
                await asyncio.sleep(1)
                return True
            
            try:
                if not state.session_manager.vector_store:
                    console.print(f"[{Colors.WARNING}]Semantic search requires ChromaDB[/]")
                    await asyncio.sleep(1)
                    return True
                
                results = await state.session_manager.find_relevant_context(
                    query=subarg,
                    max_results=5
                )
                
                if results:
                    console.print(f"\n[{Colors.PRIMARY}] SEARCH RESULTS [/]\n")
                    for i, r in enumerate(results, 1):
                        similarity = r.get("similarity", 0)
                        content = r.get("content", "")[:100]
                        console.print(
                            f"  [{Colors.DIM}]{i}.[/] "
                            f"[{Colors.ACCENT}]{similarity:.2f}[/] "
                            f"[{Colors.TEXT_PRIMARY}]{content}...[/]"
                        )
                else:
                    console.print(f"[{Colors.DIM}]No results found[/]")
            except Exception as e:
                console.print(f"[{Colors.ERROR}]Error: {e}[/]")
        
        else:
            console.print(f"[{Colors.WARNING}]Unknown subcommand: {subcmd}[/]")
        
        await asyncio.sleep(1.5)

    elif cmd == "/ingest":
        # Ingest files into vector memory
        if not state.use_memory or not state.session_manager:
            console.print(f"[{Colors.WARNING}]Memory system not available[/]")
            await asyncio.sleep(1)
            return True
            
        target_dir = Path(arg) if arg else Path.cwd()
        if not target_dir.exists():
            console.print(f"[{Colors.ERROR}]Path not found: {target_dir}[/]")
            await asyncio.sleep(1)
            return True

        console.print(f"\n[{Colors.PRIMARY}] INGESTING CODEBASE :: {target_dir} [/]")
        console.print(f"[{Colors.DIM}]Scanning files...[/]")

        files_to_process = []
        if target_dir.is_file():
            files_to_process.append(target_dir)
        else:
            # Recursive scan, respecting hidden files (simple version)
            for path in target_dir.rglob("*"):
                if path.is_file() and not any(part.startswith(".") for part in path.parts):
                    # Filter by extension
                    if path.suffix in [".py", ".md", ".txt", ".js", ".ts", ".rs", ".go", ".c", ".cpp", ".h", ".json", ".toml", ".sh"]:
                        files_to_process.append(path)

        total_files = len(files_to_process)
        console.print(f"[{Colors.PRIMARY}]Found {total_files} files suitable for ingestion.[/]")
        
        processed = 0
        errors = 0
        
        import uuid
        
        # Batch processing could be better, but let's do simple sequential for now to show progress
        for file_path in files_to_process:
            try:
                # Read content
                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue # Skip binary
                
                if not content.strip():
                    continue

                # Create embedding via Ollama
                embedding = await client.embed(content[:2000]) # Truncate for embedding model limit
                
                if embedding:
                    # Save to vector store
                    # We use file path as ID to allow updates
                    doc_id = str(file_path.absolute())
                    
                    await state.session_manager.vector_store.add_message(
                        message_id=doc_id,
                        content=f"File: {file_path.name}\nPath: {file_path}\n\n{content}",
                        metadata={
                            "source": str(file_path),
                            "type": "code_file",
                            "session_id": state.current_session_id
                        },
                        embedding=embedding
                    )
                    processed += 1
                    console.print(f"  [{Colors.SUCCESS}]✓[/] {file_path.name}")
                else:
                    console.print(f"  [{Colors.WARNING}]⚠[/] {file_path.name} (Embedding failed)")
                    errors += 1
            
            except Exception as e:
                console.print(f"  [{Colors.ERROR}]✗[/] {file_path.name}: {e}")
                errors += 1

        console.print(f"\n[{Colors.SUCCESS}] INGESTION COMPLETE [/]")
        console.print(f"[{Colors.DIM}]Processed: {processed} | Errors: {errors}[/]")
        await asyncio.sleep(2)

    elif cmd == "/tokens":
        # Show token usage
        try:
            from .ollama_client import count_tokens

            total_tokens = 0
            for msg in state.messages:
                content = msg.get("content", "")
                if content:
                    total_tokens += count_tokens(content)

            # Add system prompt
            total_tokens += count_tokens(state.system_prompt)

            # Estimate context limit (from config)
            from .config import CONTEXT_LENGTH

            usage_percent = (total_tokens / CONTEXT_LENGTH) * 100

            # Visual bar
            bar_width = 30
            filled = int((usage_percent / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            color = (
                Colors.SUCCESS
                if usage_percent < 50
                else Colors.WARNING
                if usage_percent < 80
                else Colors.ERROR
            )

            console.print(f"\n[{Colors.PRIMARY}] CONTEXT USAGE [/]\n")
            console.print(f"  [{color}]{bar}[/] {usage_percent:.1f}%")
            console.print(f"\n  [{Colors.DIM}]Tokens: {total_tokens:,} / {CONTEXT_LENGTH:,}[/]")
            console.print(f"  [{Colors.DIM}]Messages: {len(state.messages)}[/]")

        except Exception as e:
            console.print(f"[{Colors.ERROR}]Error counting tokens: {e}[/]")

        await asyncio.sleep(2)

    else:
        console.print(f"[{Colors.WARNING}] UNKNOWN COMMAND PROTOCOL: {cmd}[/]")
        await asyncio.sleep(0.5)

    return True
