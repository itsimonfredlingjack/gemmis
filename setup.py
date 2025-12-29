#!/usr/bin/env python3
"""Setup script for GEMMIS CLI"""
from setuptools import setup, find_packages

setup(
    name="gemmis-cli",
    version="2.0.0",
    description="GEMMIS CLI - Neural Interface Terminal",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "httpx>=0.24.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "gemmis=gemmis.app:main",
        ],
    },
    python_requires=">=3.10",
    py_modules=[],
)
