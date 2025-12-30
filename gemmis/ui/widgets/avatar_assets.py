"""
GEMMIS Avatar Assets - ASCII Art for the Robot Face
"""

# 3-frame idle animation
IDLE_FRAMES = [
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀       ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [bold #00ffff]O   O[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [bold #00ffff]  ^  [/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]─────[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """,
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀       ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [dim #00ffff]O   O[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [dim #00ffff]  ^  [/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]─────[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """,
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀       ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [bold #00ffff]-   -[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [bold #00ffff]  ^  [/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]─────[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """
]

# Matrix scan style for thinking
THINKING_FRAMES = [
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀ [bold #00ff00]10110[/] ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [bold #00ff00]01001[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [bold #00ff00]11010[/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]─────[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """,
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀ [bold #00ff00]01001[/] ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [bold #00ff00]11010[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [bold #00ff00]00111[/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]─────[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """
]

# Mouth movement for speaking
SPEAKING_FRAMES = [
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀       ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [bold #00ffff]O   O[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [bold #00ffff]  ^  [/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]▄▄▄▄▄[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """,
    """
    [#ff00ff]   ▄█████████▄   [/#ff00ff]
    [#ff00ff]  ▄█▀       ▀█▄  [/#ff00ff]
    [#ff00ff] ▄█   [bold #00ffff]O   O[/]   █▄ [/#ff00ff]
    [#ff00ff] █    [bold #00ffff]  ^  [/]    █ [/#ff00ff]
    [#ff00ff] ▀█▄  [bold #ff00ff]▀▀▀▀▀[/]  ▄█▀ [/#ff00ff]
    [#ff00ff]  ▀██▄▄▄▄▄▄▄██▀  [/#ff00ff]
    """
]

# Glitch/Error
ERROR_FRAME = """
    [#ff0000]   ▄█████████▄   [/#ff0000]
    [#ff0000]  ▄█▀ [blink]ERROR[/blink] ▀█▄  [/#ff0000]
    [#ff0000] ▄█   [bold #ff0000]X   X[/]   █▄ [/#ff0000]
    [#ff0000] █    [bold #ff0000]  ^  [/]    █ [/#ff0000]
    [#ff0000] ▀█▄  [bold #ff0000]─────[/]  ▄█▀ [/#ff0000]
    [#ff0000]  ▀██▄▄▄▄▄▄▄██▀  [/#ff0000]
"""
