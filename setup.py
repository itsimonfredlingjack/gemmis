#!/usr/bin/env python3
"""Setup script for GEMMIS CLI"""
from setuptools import setup, find_packages

setup(
    name="gemmis-cli",
    version="2.1.0",
    description="GEMMIS CLI - Neural Interface Terminal",
    packages=find_packages(),
    install_requires=[
        "rich>=14.2.0",
        "textual>=0.53.0",
        "pyperclip>=1.8.0",
        "docker>=7.0.0",
        "httpx>=0.24.0",
        "psutil>=5.9.0",
        "typer[all]>=0.9.0",
        "aiosqlite>=0.19.0",
        "pydantic>=2.0.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "gemmis=gemmis.cli:app",
        ],
    },
    python_requires=">=3.10",
)
