from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from griffe import GriffeLoader, load_extensions
from pytest import fixture

from isqx import DBV
from isqx import Expr as IsqxExpr
from isqx.mkdocs.extension import (
    Definition,
    IsqxExtension,
)
from isqx.mkdocs.unit_json import build_unit_decl_table, serialize_unit_decl


@fixture(scope="module")
def objects_json() -> dict[str, Any]:
    extension = IsqxExtension(
        config={
            "definitions": (
                "isqx._iso80000",
                "isqx.aerospace",
                "isqx.usc",
                "isqx.chemistry",
            ),
            "details": (
                "isqx.details.iso80000.SPACE_AND_TIME",
                "isqx.details.iso80000.MECHANICS",
                "isqx.details.iso80000.THERMODYNAMICS",
                "isqx.details.iso80000.ELECTROMAGNETISM",
                "isqx.details.iso80000.LIGHT_AND_RADIATION",
                "isqx.details.iso80000.ACOUSTICS",
                "isqx.details.iso80000.PHYSICAL_CHEMISTRY_AND_MOLECULAR_PHYSICS",
                "isqx.details.iso80000.ATOMIC_AND_NUCLEAR_PHYSICS",
                "isqx.details.iso80000.CHARACTERISTIC_NUMBERS",
                "isqx.details.iso80000.CONDENSED_MATTER_PHYSICS",
                "isqx.details.iso80000.INFORMATION_SCIENCE_AND_TECHNOLOGY",
                "isqx.details.chemistry.PHYSICAL_CHEMISTRY",
                "isqx.details.aerospace.AEROSPACE",
            ),
        }
    )
    loader = GriffeLoader(
        extensions=load_extensions(extension),
        search_paths=[str(Path("src").resolve())],
    )
    loader.load("isqx", try_relative_path=False)

    with TemporaryDirectory() as td:
        path = extension.write_objects(td)
        return cast(dict[str, Any], json.loads(Path(path).read_text()))


def test_ft_per_min_is_inlined_in_final_objects_json(
    objects_json: dict[str, Any],
) -> None:
    units = cast(dict[str, Any], objects_json["units"])
    ft_per_min = units["isqx.aerospace.FT_PER_MIN"]

    assert ft_per_min["tag"] == "derived"
    expr = ft_per_min["data"]["expr"]
    assert expr["tag"] == "mul"

    terms = expr["data"]["terms"]
    assert terms[1] == {
        "tag": "pow",
        "data": {
            "base": {
                "tag": "ref",
                "data": {"path": "isqx.MIN", "name": "minute"},
            },
            "exponent": {
                "tag": "int",
                "data": {"text": "-1", "value": -1},
            },
        },
    }


def test_ft_resolves_to_usc_owner_in_final_objects_json(
    objects_json: dict[str, Any],
) -> None:
    units = cast(dict[str, Any], objects_json["units"])
    ft_per_min = units["isqx.aerospace.FT_PER_MIN"]
    ft_ref = ft_per_min["data"]["expr"]["data"]["terms"][0]

    assert ft_ref == {
        "tag": "ref",
        "data": {"path": "isqx.usc.FT", "name": "foot"},
    }


def test_iso_owner_is_normalized_to_public_reexport_in_final_json(
    objects_json: dict[str, Any],
) -> None:
    units = cast(dict[str, Any], objects_json["units"])
    foot = units["isqx.usc.FT"]
    meter_ref = foot["data"]["expr"]["data"]["unit"]

    assert meter_ref == {
        "tag": "ref",
        "data": {"path": "isqx.M", "name": "meter"},
    }


def _walk_unit_refs(value: object) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("tag") == "ref":
            refs.append(cast(dict[str, Any], value["data"]))
        for child in value.values():
            refs.extend(_walk_unit_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_walk_unit_refs(child))
    return refs


def test_all_generated_unit_refs_are_public(
    objects_json: dict[str, Any],
) -> None:
    refs = _walk_unit_refs(objects_json)

    assert refs
    assert all(set(ref) == {"path", "name"} for ref in refs)


def test_public_aliased_log_units_stay_ref_leaves_when_nested() -> None:
    # Assuming public aliased logarithmic units behave like any other public
    # alias: when reused inside another public declaration they remain ref
    # leaves instead of being structurally inlined.
    double_dbv = (2 * DBV).alias("double_dbv")
    definitions = {
        "isqx.DBV": Definition(DBV, None),
        "isqx.double_dbv": Definition(double_dbv, None),
    }
    unit_decls = build_unit_decl_table(
        cast(
            dict[str, IsqxExpr],
            {
                path: definition.value
                for path, definition in definitions.items()
            },
        ),
        public_definitions={
            "isqx.DBV": "isqx.DBV",
            "isqx.double_dbv": "isqx.double_dbv",
        },
    )

    decl = serialize_unit_decl(
        "isqx.double_dbv",
        unit_decls=unit_decls,
    )

    assert decl == {
        "tag": "alias",
        "data": {
            "path": "isqx.double_dbv",
            "name": "double_dbv",
            "expr": {
                "tag": "scaled",
                "data": {
                    "factor": {
                        "tag": "number",
                        "data": {
                            "value": {
                                "tag": "int",
                                "data": {"text": "2", "value": 2},
                            }
                        },
                    },
                    "unit": {
                        "tag": "ref",
                        "data": {"path": "isqx.DBV", "name": "dBV"},
                    },
                },
            },
            "allowPrefix": False,
        },
    }
