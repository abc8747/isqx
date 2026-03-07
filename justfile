check:
    uv run --python 3.9 ruff check src tests
    uv run --python 3.9 ruff format --check src tests
    uv run --python 3.9 mypy src tests
    # mkdocs doesn't detect wikipedia links that end with `)`
    rg -i '[^<]https://en.wikipedia.org/wiki/.*\(.*\)[^>#]' -g '!scripts/' --no-heading

check-katex:
    rg -i '_\{([A-Za-z_ ,]+)\}' src/isqx/details --no-heading
    rg -i '\"\w_([A-Za-z_ ,]+)\w*\"' src/isqx/details --no-heading

fix:
    uv run --python 3.9 ruff check --fix src tests
    uv run --python 3.9 ruff format src tests
    cd src/isqx_vis && pnpm run fmt

_sync-docs:
    printf '%s\n' '<!-- DO NOT EDIT! CHANGES WILL BE LOST. edit `README.md` and run `just docs-build` instead. -->' > docs/index.md
    sed 's#](docs/assets/#](assets/#g' README.md >> docs/index.md
    printf '%s\n' '<!-- DO NOT EDIT! CHANGES WILL BE LOST. edit `CONTRIBUTING.md` and run `just docs-build` instead. -->' > docs/contributing.md
    cat CONTRIBUTING.md >> docs/contributing.md

_build-vis:
    if [ ! -d src/isqx_vis/node_modules ]; then echo 'src/isqx_vis/node_modules not found; run pnpm install in src/isqx_vis' >&2; exit 1; fi
    cd src/isqx_vis && pnpm build
    rsync -a --exclude=index.html src/isqx_vis/dist/ site/
    cp src/isqx_vis/dist/index.html site/vis.html

docs-build:
    just _sync-docs
    uv run --group docs --python 3.10 zensical build --config-file mkdocs.yml
    uv run --group docs --python 3.10 python -c "from isqx.mkdocs.extension import write_objects_from_config; write_objects_from_config('mkdocs.yml')"
    just _build-vis

preview:
    just docs-build
    npx http-server site -p 8080 -c-1 --brotli --gzip
