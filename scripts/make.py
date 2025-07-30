#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer",
# ]
# ///

import os

import typer

from docs import copy_docs_file

app = typer.Typer(no_args_is_help=True)

app.command()(copy_docs_file)


@app.command()
def check() -> None:
    os.system("uv run --python 3.9 ruff check src tests")
    os.system("uv run --python 3.9 ruff format --check src tests")
    os.system("uv run --python 3.9 mypy src tests")
    # mkdocs doesn't detect wikipedia links that end with `)`
    os.system(
        r"rg -i '[^<]https://en.wikipedia.org/wiki/.*\(.*\)[^>#]' -g '!scripts/' --no-heading"
    )


@app.command()
def check_katex() -> None:
    r"""Highlight underscores in katex"""
    os.system(r"rg -i '_\\{([A-Za-z_ ,]+)\\}' src/isq/details --no-heading")
    os.system(r"rg -i '\"\w_([A-Za-z_ ,]+)\w*\"' src/isq/details --no-heading")


@app.command()
def fix() -> None:
    os.system("uv run --python 3.9 ruff check --fix src tests")
    os.system("uv run --python 3.9 ruff format src tests")


if __name__ == "__main__":
    app()
