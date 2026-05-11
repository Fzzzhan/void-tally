#!/usr/bin/env python3
"""
VoidTally Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="voidtally",
    version="0.1.0",
    description="Non-intrusive AI CLI performance observation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="fengze",
    author_email="fengze@example.com",
    url="https://github.com/Fzzzhan/void-tally",
    project_urls={
        "Bug Reports": "https://github.com/Fzzzhan/void-tally/issues",
        "Source": "https://github.com/Fzzzhan/void-tally",
        "Documentation": "https://github.com/Fzzzhan/void-tally/blob/main/README.md",
    },
    license="MIT",
    keywords="ai cli performance monitoring tracking void time",
    python_requires=">=3.7",
    py_modules=[
        "voidtally",
        "void_observer",
        "void_tracker",
        "void_storage",
        "void_dashboard",
        "void_watcher",
        "void_git",
        "void_snapshot",
        "void_char_counter",
        "void_mailer",
        "void_scheduler",
    ],
    install_requires=[
        "rich>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "voidtally=voidtally:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
)
