#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "cmocean",
#     "numpy",
#     "matplotlib",
#     "pyqt6",
#     "colorspacious"
# ]
# ///
from __future__ import annotations

from typing import Any, Callable, Generator, NamedTuple, TypedDict

import cmocean
import matplotlib.pyplot as plt
import numpy as np
from colorspacious import cspace_converter
from matplotlib import gridspec
from matplotlib.lines import Line2D
from numpy.typing import NDArray

srgb_to_cam02 = cspace_converter("sRGB1", "CAM02-UCS")
cam02_to_srgb = cspace_converter("CAM02-UCS", "sRGB1")


def get_lightness_values(rgb_data: NDArray) -> NDArray:
    rgb_clipped = np.clip(rgb_data, 0, 1)
    lab = srgb_to_cam02(rgb_clipped[np.newaxis, :, :])
    return lab[0, :, 0]


def cam02(
    *,
    lightness_factor: float,
    red_green_factor: float = 1.0,
    yellow_blue_factor: float = 1.0,
) -> Callable[[NDArray], NDArray]:
    def cam02_(data_rgb: NDArray) -> NDArray:
        jab = srgb_to_cam02(data_rgb)  # (N, (lightness,red-green,yellow-blue))
        jab[:, 0] *= lightness_factor
        jab[:, 1] *= red_green_factor
        jab[:, 2] *= yellow_blue_factor
        darkened_rgb = cam02_to_srgb(jab)
        return np.clip(darkened_rgb, 0, 1)

    return cam02_


def phase_to_rainbow(v):
    return np.vstack([v[40:], v[:40]])[::-1]


class FitResult(NamedTuple):
    y_fit: NDArray
    coeffs_fit: NDArray


def fit(x, y, degree: int) -> FitResult:
    num_coeffs = degree + 1
    A = np.vander(x, degree + 1)
    C = np.vander(x[[0, -1]], degree + 1)
    H = A.T @ A
    num_constraints = C.shape[0]
    mat = np.block(
        [[H, C.T], [C, np.zeros((num_constraints, num_constraints))]]
    )

    y_fit = np.zeros_like(y)
    coeffs_fit = np.zeros((degree + 1, y.shape[1]))

    for i in range(y.shape[1]):
        b = y[:, i]
        d = y[[0, -1], i]
        rhs = np.concatenate([A.T @ b, d])

        solution = np.linalg.solve(mat, rhs)
        coeffs = solution[:num_coeffs]
        coeffs_fit[:, i] = coeffs
        y_fit[:, i] = A @ coeffs

    return FitResult(y_fit, coeffs_fit)


def camel(snake_str):
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.capitalize, others)])


def gen_js(
    coeffs_fit: NDArray,
    out_name: str,
    needs_clamp: bool,
    *,
    typescript: bool = True,
) -> Generator[str, None, None]:
    assert " " not in out_name, out_name
    anno_in = ": number" if typescript else ""
    anno_out = ": [number, number, number]" if typescript else ""
    yield f"const {camel(out_name)} = (x{anno_in}){anno_out} => [\n"
    assert coeffs_fit.shape[1] == 3
    for i in range(3):
        yield "  "
        coeffs_ch = coeffs_fit[::-1, i]
        if needs_clamp:
            yield "clamp("
        for j, coeff in enumerate(coeffs_ch):
            if j > 0:
                if not coeff:
                    continue
                yield " + " if coeff > 0 else " - "
            yield f"{abs(coeff)}"
            if j == 0:
                continue
            yield " * x"
            if j > 1:
                yield f" ** {j}"
        if needs_clamp:
            yield ")"
        if i < 2:
            yield ","
        yield "\n"
    yield "]"


class Result(TypedDict):
    name: str
    degree: int
    coeffs: list[list[float]]
    javascript: str


def main(
    from_cmap_name: str,
    degree: int,
    *,
    out_name: str,
    preprocess: Callable[[NDArray], NDArray] | None = None,
    fit: Callable[[Any, Any, int], FitResult] = fit,
    show_plot: bool = False,
) -> Result:
    cmap = cmocean.cm.cmap_d[from_cmap_name]
    x = np.linspace(0, 1, 256)
    y_orig = cmap(x)[:, :3]
    if preprocess is not None:
        y_orig = preprocess(y_orig)
    result = fit(x, y_orig * 0xFF, degree)
    needs_clamp = np.any(result.y_fit < 0) or np.any(result.y_fit > 0xFF)
    if show_plot:
        plot(
            x=x,
            y_orig=y_orig,
            y_fit=result.y_fit,
            out_name=out_name,
            degree=degree,
        )
    return {
        "name": out_name,
        "degree": degree,
        "coeffs": result.coeffs_fit.T.tolist(),
        "javascript": "".join(gen_js(result.coeffs_fit, out_name, needs_clamp)),
    }


def plot(
    x: NDArray, y_orig: NDArray, y_fit: NDArray, out_name: str, degree: int
) -> None:
    x_0xff = x * 0xFF
    fig = plt.figure(figsize=(10, 10))
    fig.suptitle(f"`{out_name}` colormap fit (degree {degree})", fontsize=16)
    gs = gridspec.GridSpec(4, 1, height_ratios=[1, 1, 5, 5], hspace=0)

    ax_orig = fig.add_subplot(gs[0])
    ax_orig.imshow(y_orig[np.newaxis, :, :], aspect="auto")
    ax_orig.set_xlim(0, 0xFF)
    ax_orig.set_xticks([])
    ax_orig.set_yticks([])
    ax_orig.set_ylabel("original")
    ax_orig.yaxis.label.set(rotation="horizontal", ha="right")

    ax_fit = fig.add_subplot(gs[1], sharex=ax_orig)
    ax_fit.imshow(y_fit[np.newaxis, :, :] / 0xFF, aspect="auto")
    ax_fit.set_yticks([])
    ax_fit.set_ylabel("fitted")
    ax_fit.yaxis.label.set(rotation="horizontal", ha="right")

    ax_rgb = fig.add_subplot(gs[2], sharex=ax_orig)
    colors = ["red", "green", "blue"]
    for i, color in enumerate(colors):
        ax_rgb.plot(x_0xff, y_orig[:, i] * 0xFF, color=color)
        ax_rgb.plot(x_0xff, y_fit[:, i], "--", color=color)

    legend_elements = [
        Line2D([0], [0], color="k", linestyle="-", label="orig"),
        Line2D([0], [0], color="k", linestyle="--", label="fit"),
    ]
    ax_rgb.legend(handles=legend_elements)
    ax_rgb.set_ylim(0, 255)
    ax_rgb.set_ylabel("rgb")
    ax_rgb.grid(True, linestyle=":")

    ax_lightness = fig.add_subplot(gs[3], sharex=ax_orig)
    l_orig = get_lightness_values(y_orig)
    l_fit = get_lightness_values(y_fit / 0xFF)
    ax_lightness.plot(x_0xff, l_orig, "k-", label="orig")
    ax_lightness.plot(x_0xff, l_fit, "r--", label="fit")
    ax_lightness.set_xticks(np.arange(0, 256, 16))
    ax_lightness.set_xlabel("index")
    ax_lightness.set_ylim(0, 100)
    ax_lightness.set_ylabel("lightness")
    ax_lightness.grid(True, linestyle=":")
    ax_lightness.legend(loc="best")

    fig.tight_layout()
    plt.show()


def logo(
    from_cmap_name: str,
    preprocess: Callable[[NDArray], NDArray] | None = None,
) -> Generator[str, None, None]:
    cmap = cmocean.cm.cmap_d[from_cmap_name]
    num_circles = 7
    points = np.linspace(0, 0.7, num_circles)
    colors = cmap(points)
    rgb = colors[:, :3]
    if preprocess:
        rgb = preprocess(rgb)
    yield '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">\n'
    t0 = np.pi / num_circles / 2
    t = np.linspace(0, 2 * np.pi, num_circles, endpoint=False) + t0
    radius = 14
    d = radius / np.sin(np.pi / num_circles)
    for i in range(num_circles):
        cx = 50 + d * np.cos(t[i])
        cy = 50 + d * np.sin(t[i])
        r, g, b = np.clip(rgb[i], 0, 1)
        fill_color = f"rgb({int(r * 255)},{int(g * 255)},{int(b * 255)})"
        yield f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{fill_color}"/>'
    yield "</svg>"


if __name__ == "__main__":
    from pathlib import Path

    with open(
        Path(__file__).parent.parent
        / "src"
        / "isqx_vis"
        / "assets"
        / "logo.svg",
        "w",
    ) as f:
        f.write("".join(logo("phase", preprocess=phase_to_rainbow)))
    # exit()
    results = [
        main(
            from_cmap_name="phase",
            degree=7,
            out_name="phase_rainbow",
            preprocess=phase_to_rainbow,
            show_plot=True,
        ),
        main(
            from_cmap_name="phase",
            degree=7,
            out_name="phase_rainbow_dark04",
            preprocess=lambda y: cam02(lightness_factor=0.4)(
                phase_to_rainbow(y)
            ),
            show_plot=True,
        ),
    ]
    for r in results:
        print(r["javascript"])
    # import json

    # with open(Path(__file__).parent / "cmap.json", "w") as f:
    #     json.dump(
    #         [result for result in results],
    #         f,
    #         indent=2,
    #     )
