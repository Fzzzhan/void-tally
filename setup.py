#!/usr/bin/env python3
"""
VoidTally 安装脚本
"""

from setuptools import setup, find_packages

setup(
    name="voidtally",
    version="0.1.0",
    description="Non-intrusive AI CLI performance observation tool",
    author="fengze",
    python_requires=">=3.7",
    py_modules=[
        "voidtally",
        "void_observer",
        "void_tracker",
        "void_storage",
        "void_dashboard",
    ],
    entry_points={
        "console_scripts": [
            "voidtally=voidtally:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
