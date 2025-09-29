"""Setup configuration for Rekordbox Streaming Tag Exporter."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rekordbox-tag-exporter",
    version="0.1.0",
    author="DJ Tools",
    description="Export Rekordbox streaming tracks filtered by tags to CSV",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rekordbox-tag-exporter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pyrekordbox>=0.3.0",
        "click>=8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
            "black",
            "ruff",
            "mypy",
            "pre-commit",
        ]
    },
    entry_points={
        "console_scripts": [
            "rekordbox-export=cli.export_command:main",
        ],
    },
)