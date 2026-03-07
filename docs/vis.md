
# Visualiser

Here is an interactive visualisation of (most) quantity kinds. The standalone
page can be found at [`/vis.html`](https://abc8747.github.io/isqx/vis.html?autoLoad).

<!-- markdownlint-disable MD033 -->
<iframe
  src="https://abc8747.github.io/isqx/vis.html?autoLoad"
  sandbox="allow-scripts allow-same-origin"
  loading="lazy"
  title="ISQX Visualization"
  style="width: 100%; height: 768px; border: 1px solid var(--md-typeset-table-color);">
</iframe>
<!-- markdownlint-enable MD033 -->

Shift click to select multiple nodes.

## Implementation

Our Zensical/mkdocstrings integration layer uses static and dynamic analysis to
collect all quantity kinds, constants and units into a single `objects.json`.

The visualiser is written in [solidjs](https://github.com/solidjs/solid) and D3.

When data is loaded, the size of the node is first determined by the number of
incoming links ("referenced by" in equations). A hierarchy is first formed and
the a force simulation is performed.

The colour of the nodes is determined by the order they are defined in code.

## TODO

- clickable links for units
- show numerical value for constants
- cross-ref to this items in this documentation
