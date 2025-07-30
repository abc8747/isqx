#!/usr/bin/env -S uv run --script
from functools import partial
from pathlib import Path

path_root = Path(__file__).parent.parent

FILENAME_INDEX = "index"
FILENAME_CONTRIBUTING = "contributing"


def copy_docs_file(path_in: Path, path_out: Path) -> None:
    """Copy a file from `path_in` to `path_out` with warnings.

    Should be used to sync the homepage in the docs with the one from
    `path_root/README.md`.

    - `base_path: !relative $config_dir` and `--8<-- "README.md"` doesn't work
      and it causes crossrefs to break.
    - symlinking `docs/README.md` to `../README.md` breaks images as well.
    - https://stackoverflow.com/questions/75716969/mkdocs-with-readme-as-index-containing-images-with-broken-links
    - https://stackoverflow.com/questions/73828765/mkdocs-how-to-link-to-the-same-images-in-readme-md-and-docs-index-md-at-the
    """
    with open(path_in, "r") as f:
        readme_content = f.read()
    output = (
        "<!-- DO NOT EDIT! CHANGES WILL BE LOST. edit `README.md` and"
        + f" run `{Path(__file__).relative_to(path_root)}` instead. -->\n"
        + readme_content.replace("](docs/assets/", "](assets/")
    )
    with open(path_out, "w+") as f:
        content = f.read()
        if content != output:
            f.write(output)


copy_readme = partial(
    copy_docs_file,
    path_in=path_root / "README.md",
    path_out=path_root / "docs" / f"{FILENAME_INDEX}.md",
)

copy_contributing = partial(
    copy_docs_file,
    path_in=path_root / "CONTRIBUTING.md",
    path_out=path_root / "docs" / f"{FILENAME_CONTRIBUTING}.md",
)

# mkdocs events


def on_pre_build(config) -> None:  # type: ignore
    copy_readme()
    copy_contributing()


if __name__ == "__main__":
    copy_readme()
    copy_contributing()
