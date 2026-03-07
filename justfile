docs_python := "uv run --group docs --python 3.10"
vis_dir := "src/isqx_vis"

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

_require-vis:
    if [ ! -d {{ vis_dir }}/node_modules ]; then echo '{{ vis_dir }}/node_modules not found; run pnpm install in {{ vis_dir }}' >&2; exit 1; fi

_stage-vis-data:
    if [ ! -f site/assets/objects.json ]; then echo 'site/assets/objects.json not found; run just docs-build once first' >&2; exit 1; fi
    cp site/assets/objects.json {{ vis_dir }}/assets/objects.json

_build-vis: _require-vis
    cd {{ vis_dir }} && pnpm build
    rsync -a --exclude=index.html {{ vis_dir }}/dist/ site/
    cp {{ vis_dir }}/dist/index.html site/vis.html

vis-dev: _require-vis _stage-vis-data
    cd {{ vis_dir }} && pnpm run dev:autoload

docs-build:
    just _sync-docs
    {{ docs_python }} zensical build --config-file mkdocs.yml
    {{ docs_python }} python -c "from isqx.mkdocs.extension import write_objects_from_config; write_objects_from_config('mkdocs.yml')"
    just _build-vis

preview:
    just docs-build
    npx http-server site -p 8080 -c-1 --brotli --gzip
