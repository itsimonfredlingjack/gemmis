"""
GEMMIS UI Input - Advanced input handling with prompt_toolkit
"""

import os
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

class GemmisCompleter(Completer):
    """
    Custom completer that provides:
    1. Command completion (starts with /)
    2. Path completion (for file arguments)
    """
    def __init__(self):
        self.commands = [
            "/help", "/clear", "/save", "/load", "/list", "/export",
            "/sessions", "/session", "/tokens", "/system", "/health",
            "/top", "/theme", "/persona", "/model", "/config", "/quit",
            "/ingest"
        ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # 1. Command completion
        if text.startswith("/"):
            if " " not in text:
                for cmd in self.commands:
                    if cmd.startswith(text):
                        yield Completion(cmd, start_position=-len(text))
            return

        # 2. Path completion (triggered if we see a path separator or it looks like an arg)
        # Simple heuristic: look at the last word
        word = document.get_word_before_cursor(WORD=True)
        
        if "/" in word or word == "." or word == "..":
            # Attempt path completion
            path_str = word
            
            # Expand ~
            expanded_path = os.path.expanduser(path_str)
            
            if os.path.isdir(expanded_path):
                dirname = expanded_path
                basename = ""
            else:
                dirname = os.path.dirname(expanded_path)
                basename = os.path.basename(expanded_path)
            
            # If dirname is empty, use current dir
            if not dirname:
                dirname = "."
                
            try:
                for name in os.listdir(dirname):
                    if name.startswith(basename):
                        # Add trailing slash for directories
                        full_path = os.path.join(dirname, name)
                        display = name
                        if os.path.isdir(full_path):
                            display += "/"
                        
                        yield Completion(display, start_position=-len(basename))
            except Exception:
                pass

def get_input_session(colors):
    """
    Create a configured PromptSession
    """
    # Create style based on current theme
    style_dict = {
        'prompt': f'{colors.PRIMARY} bold',
        'prompt_arg': f'{colors.SECONDARY}',
    }
    
    style = Style.from_dict(style_dict)
    
    session = PromptSession(
        completer=GemmisCompleter(),
        style=style,
        complete_while_typing=True,
    )
    
    return session
