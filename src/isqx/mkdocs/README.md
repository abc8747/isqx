# Zensical and mkdocstrings-python integration

Previously, our documentation used `mkdocs-material` (now [deprecated](https://squidfunk.github.io/mkdocs-material/blog/2025/11/05/zensical/)) + `mkdocstrings` (now in [maintenance mode](https://pawamoy.github.io/posts/sunsetting-the-sponsorware-strategy/)).
It is succeeded by Zensical.

Notes during migration:

- Zensical owns the outer site build.
- `mkdocstrings-python` still owns Python API extraction/rendering.
- We no longer hook into the MkDocs lifecycle events, but instead add repo-
  specific API enrichment on top of that path.

`isqx` adds several things on top of the baseline Zensical + mkdocstrings path:

- `isqx.mkdocs.extension` registers a Griffe extension that inspects our unit,
  quantity-kind, and details definitions during API extraction.
- That extension injects extra mkdocstrings metadata into collected objects so
  the rendered API docs can show: quantity symbols, equations and assumptions,
  Wikidata links.
- The same module owns the `objects.json` generation logic, which `just docs-build`
  invokes explicitly after the Zensical build so the visualizer can consume the
  docs-derived object graph.
- `templates/material/isqx` overrides mkdocstrings fragment templates to render
  the extra `isqx` metadata.
- `assets/` contains the local JS/CSS that Zensical copies via
  `theme.custom_dir`, including the KaTeX/highlighting layer used by those
  enriched API fragments.
