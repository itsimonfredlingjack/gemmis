import ast
import traceback

with open("gemmis/app.py", "r") as f:
    code = f.read()

try:
    ast.parse(code)
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError: {e.msg}")
    print(f"Line: {e.lineno}")
    print(f"Offset: {e.offset}")
    print(f"Text: {e.text}")
