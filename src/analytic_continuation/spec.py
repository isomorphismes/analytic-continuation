"""Load and validate the JSON contract shared by the renderer and Wegert."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .complex_values import ComplexValueError, parse_complex


class MovieSpecError(ValueError):
    """Raised when a movie specification is malformed."""


@dataclass(frozen=True)
class ContinuationViewSpec:
    path: tuple[complex, ...]
    patch_reveal_seconds: float


@dataclass(frozen=True)
class ViewSpec:
    center: complex = 0j
    half_height: float = 4.0
    grid_step: float = 1.0
    mode: str = "whole"
    continuation: ContinuationViewSpec | None = None


@dataclass(frozen=True)
class AnimationSpec:
    open_seconds: float = 5.0
    hold_seconds: float = 1.0
    close_seconds: float = 5.0
    close: bool = True
    curve_density: int = 64
    output_margin: float = 0.94


@dataclass(frozen=True)
class MovieSpec:
    function: Mapping[str, Any]
    view: ViewSpec
    animation: AnimationSpec
    probes: tuple[complex, ...]
    title: str | None = None
    schema: str = "analytic-continuation/movie-v1"


def load_movie_spec(path: str | Path) -> MovieSpec:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise MovieSpecError(f"movie specification does not exist: {source}") from error
    except json.JSONDecodeError as error:
        raise MovieSpecError(
            f"invalid JSON in {source}: line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    return parse_movie_spec(raw)


def parse_movie_spec(raw: Any) -> MovieSpec:
    if not isinstance(raw, Mapping):
        raise MovieSpecError("movie specification must be an object")

    allowed = {"schema", "function", "view", "animation", "probes", "title"}
    _reject_unknown("movie specification", raw, allowed)

    schema = raw.get("schema", "analytic-continuation/movie-v1")
    if schema != "analytic-continuation/movie-v1":
        raise MovieSpecError(
            "schema must be 'analytic-continuation/movie-v1'"
        )

    function = raw.get("function")
    if not isinstance(function, Mapping):
        raise MovieSpecError("function is required and must be an object")

    title = raw.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        raise MovieSpecError("title must be a non-empty string when present")

    return MovieSpec(
        schema=schema,
        function=dict(function),
        view=_parse_view(raw.get("view", {})),
        animation=_parse_animation(raw.get("animation", {})),
        probes=_parse_probes(raw.get("probes", [])),
        title=title,
    )


def _parse_view(raw: Any) -> ViewSpec:
    if not isinstance(raw, Mapping):
        raise MovieSpecError("view must be an object")
    _reject_unknown(
        "view",
        raw,
        {"center", "half_height", "grid_step", "mode", "continuation"},
    )

    try:
        center = parse_complex(raw.get("center", [0.0, 0.0]), "view.center")
    except ComplexValueError as error:
        raise MovieSpecError(str(error)) from error

    half_height = _positive_real(raw.get("half_height", 4.0), "view.half_height")
    grid_step = _positive_real(raw.get("grid_step", 1.0), "view.grid_step")

    mode = raw.get("mode", "whole")
    if not isinstance(mode, str) or mode not in {"whole", "continuation"}:
        raise MovieSpecError("view.mode must be 'whole' or 'continuation'")

    if mode == "whole":
        if "continuation" in raw:
            raise MovieSpecError(
                "view.continuation is only allowed when view.mode is 'continuation'"
            )
        continuation = None
    else:
        if "continuation" not in raw:
            raise MovieSpecError(
                "view.continuation is required when view.mode is 'continuation'"
            )
        continuation = _parse_continuation_view(raw["continuation"])

    return ViewSpec(
        center=center,
        half_height=half_height,
        grid_step=grid_step,
        mode=mode,
        continuation=continuation,
    )


def _parse_continuation_view(raw: Any) -> ContinuationViewSpec:
    if not isinstance(raw, Mapping):
        raise MovieSpecError("view.continuation must be an object")
    _reject_unknown(
        "view.continuation",
        raw,
        {"path", "patch_reveal_seconds"},
    )

    path_values = raw.get("path")
    if not isinstance(path_values, Sequence) or isinstance(
        path_values, (str, bytes, bytearray)
    ):
        raise MovieSpecError("view.continuation.path must be a list of complex centers")
    if not path_values:
        raise MovieSpecError("view.continuation.path must not be empty")

    try:
        path = tuple(
            parse_complex(value, f"view.continuation.path[{index}]")
            for index, value in enumerate(path_values)
        )
    except ComplexValueError as error:
        raise MovieSpecError(str(error)) from error

    if "patch_reveal_seconds" not in raw:
        raise MovieSpecError("view.continuation.patch_reveal_seconds is required")
    patch_reveal_seconds = _positive_real(
        raw["patch_reveal_seconds"],
        "view.continuation.patch_reveal_seconds",
    )
    return ContinuationViewSpec(
        path=path,
        patch_reveal_seconds=patch_reveal_seconds,
    )


def _parse_animation(raw: Any) -> AnimationSpec:
    if not isinstance(raw, Mapping):
        raise MovieSpecError("animation must be an object")
    _reject_unknown(
        "animation",
        raw,
        {
            "open_seconds",
            "hold_seconds",
            "close_seconds",
            "close",
            "curve_density",
            "output_margin",
        },
    )

    close = raw.get("close", True)
    if not isinstance(close, bool):
        raise MovieSpecError("animation.close must be a boolean")

    curve_density = raw.get("curve_density", 64)
    if isinstance(curve_density, bool) or not isinstance(curve_density, int):
        raise MovieSpecError("animation.curve_density must be an integer")
    if not 8 <= curve_density <= 500:
        raise MovieSpecError("animation.curve_density must be between 8 and 500")

    output_margin = _positive_real(raw.get("output_margin", 0.94), "animation.output_margin")
    if output_margin > 1.0:
        raise MovieSpecError("animation.output_margin must not exceed 1")

    return AnimationSpec(
        open_seconds=_nonnegative_real(
            raw.get("open_seconds", 5.0), "animation.open_seconds"
        ),
        hold_seconds=_nonnegative_real(
            raw.get("hold_seconds", 1.0), "animation.hold_seconds"
        ),
        close_seconds=_nonnegative_real(
            raw.get("close_seconds", 5.0), "animation.close_seconds"
        ),
        close=close,
        curve_density=curve_density,
        output_margin=output_margin,
    )


def _parse_probes(raw: Any) -> tuple[complex, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise MovieSpecError("probes must be a list of complex input values")
    try:
        return tuple(
            parse_complex(value, f"probes[{index}]")
            for index, value in enumerate(raw)
        )
    except ComplexValueError as error:
        raise MovieSpecError(str(error)) from error


def _positive_real(value: Any, field_name: str) -> float:
    number = _nonnegative_real(value, field_name)
    if number <= 0:
        raise MovieSpecError(f"{field_name} must be greater than 0")
    return number


def _nonnegative_real(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MovieSpecError(f"{field_name} must be a real number")
    number = float(value)
    if not math.isfinite(number):
        raise MovieSpecError(f"{field_name} must be finite")
    if number < 0:
        raise MovieSpecError(f"{field_name} must not be negative")
    return number


def _reject_unknown(place: str, raw: Mapping[Any, Any], allowed: set[str]) -> None:
    unknown = set(raw) - allowed
    if unknown:
        names = ", ".join(sorted(str(name) for name in unknown))
        raise MovieSpecError(f"{place} has unknown fields: {names}")
