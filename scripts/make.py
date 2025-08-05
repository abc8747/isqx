#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer",
# ]
# ///

import os
from pathlib import Path
from typing import Iterable

import typer

from docs import copy_docs_file

PATH_ROOT = Path(__file__).parent.parent
PATH_VIS = PATH_ROOT / "src" / "isqx_vis"

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
    os.system(r"rg -i '_\\{([A-Za-z_ ,]+)\\}' src/isqx/details --no-heading")
    os.system(r"rg -i '\"\w_([A-Za-z_ ,]+)\w*\"' src/isqx/details --no-heading")


@app.command()
def fix() -> None:
    os.system("uv run --python 3.9 ruff check --fix src tests")
    os.system("uv run --python 3.9 ruff format src tests")
    os.system(f"cd {PATH_VIS} && pnpm run fmt")


#
# for vis
#
PATH_DUMP = PATH_ROOT / "scripts" / "dump.sh"
EXCLUDE_VIS = [
    "pnpm-lock.yaml",
    "vite.config.ts",
    "tsconfig.json",
    ".prettier*",
    "src/cmap.ts",
    "assets/*",
]
EXCLUDE_ALL = [
    "src/isqx/py.typed",
    "src/isqx/_citations.py",
    "docs/assets/",
    *(f"src/isqx_vis/{fp}" for fp in EXCLUDE_VIS),
]

copy = typer.Typer(no_args_is_help=True)
app.add_typer(copy, name="copy")


def _g(files: Iterable[str]) -> str:
    return " ".join(f'-g "!{file}"' for file in files)


def xclip(cmd: Iterable[str]) -> str:
    return f"{cmd} | xclip -sel clipboard"


@copy.command()
def web(exclude: list[str] = EXCLUDE_VIS) -> None:
    g = _g(exclude)
    os.system(xclip(f"cd {PATH_VIS} && bash {PATH_DUMP} {g}"))


@copy.command()
def all(exclude: list[str] = EXCLUDE_ALL, slim: bool = False) -> None:
    g = _g(
        exclude
        + (["src/isqx/details/", "src/isqx/_iso80000.py"] if slim else [])
    )
    os.system(
        xclip(
            f"cd {PATH_ROOT} && bash {PATH_DUMP} README.md mkdocs.yml docs src {g}"
        )
    )


@app.command()
def preview() -> None:
    os.system(
        "uv run mkdocs build && http-server site -p 8080 -c-1 --brotli --gzip"
    )


if __name__ == "__main__":
    app()
