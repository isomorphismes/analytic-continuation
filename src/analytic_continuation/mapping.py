"""Turn unbounded complex maps into finite movie coordinates."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from .functions import ComplexEvaluator


@dataclass(frozen=True)
class ViewBox:
    center: complex
    half_width: float
    half_height: float
    margin: float = 0.94


def make_visible_map(evaluator: ComplexEvaluator, view: ViewBox) -> Callable[[complex], complex]:
    """Evaluate and clip a complex map to the visible rectangle.

    Poles and overflows are sent to the boundary in the direction of the
    input point.  This keeps every Manim control point finite; it is a drawing
    rule, not a replacement value for the mathematical function.
    """

    def visible_map(value: complex) -> complex:
        try:
            output = complex(evaluator(value))
        except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError):
            return _boundary_in_input_direction(value, view)

        if not _is_finite(output):
            return _boundary_in_input_direction(value, view)
        return clip_to_view(output, view)

    return visible_map


def clip_to_view(value: complex, view: ViewBox) -> complex:
    delta = value - view.center
    x_limit = view.half_width * view.margin
    y_limit = view.half_height * view.margin

    scale = 1.0
    if abs(delta.real) > x_limit:
        scale = min(scale, x_limit / abs(delta.real))
    if abs(delta.imag) > y_limit:
        scale = min(scale, y_limit / abs(delta.imag))
    return view.center + scale * delta


def _boundary_in_input_direction(value: complex, view: ViewBox) -> complex:
    direction = value - view.center
    if direction == 0 or not _is_finite(direction):
        direction = 1 + 0j
    far_away = view.center + direction * 1.0e100
    return clip_to_view(far_away, view)


def _is_finite(value: complex) -> bool:
    return math.isfinite(value.real) and math.isfinite(value.imag)
