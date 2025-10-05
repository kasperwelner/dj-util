"""Setup configuration for Rekordbox."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dj-tool",
    version="0.1.0",
    author="DJ Tools",
    description="DJ Tool Suite for Rekordbox management (export, link local files with optional conversion, file matching, and Bandcamp wishlist automation)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dj-tool",
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
        "selenium>=4.0.0",
        "webdriver-manager>=4.0.0",
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
            "dj-tool=cli.__main__:main",
        ],
    },
)