"""Pure planning for a disc-by-disc continuation visualization."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .functions import ComplexFunction


class ContinuationPlanError(ValueError):
    """Raised when the requested path cannot be justified by known singularities."""


@dataclass(frozen=True)
class ContinuationDisc:
    """One Taylor disc centered on a point of the requested path."""

    center: complex
    radius: float


def plan_continuation_discs(
    function: ComplexFunction,
    path: Sequence[complex],
) -> tuple[ContinuationDisc, ...]:
    """Plan maximal pole-free Taylor discs along ``path``.

    This planner verifies only the geometry of a continuation visualization.
    It does not calculate a Taylor germ or use one disc to compute values in
    the next disc.  The renderer continues to obtain values from the selected
    closed-form evaluator.
    """

    if not path:
        raise ContinuationPlanError("continuation path must contain at least one center")

    if function.branch_points:
        points = ", ".join(_format_complex(point) for point in function.branch_points)
        raise ContinuationPlanError(
            f"{function.label} has branch point(s) at {points}; "
            "branch tracking would be needed for continuation mode"
        )

    if not function.finite_singularities_complete:
        raise ContinuationPlanError(
            f"{function.label} cannot use continuation mode because its finite "
            "singularities are not completely represented"
        )

    discs: list[ContinuationDisc] = []
    for index, center in enumerate(path):
        if not math.isfinite(center.real) or not math.isfinite(center.imag):
            raise ContinuationPlanError(
                f"continuation path[{index}] must be a finite complex center"
            )

        if function.poles:
            radius = min(abs(center - pole) for pole in function.poles)
        else:
            radius = math.inf

        if radius == 0:
            raise ContinuationPlanError(
                f"continuation path[{index}] is the pole {_format_complex(center)}"
            )

        if discs:
            preceding = discs[-1]
            step = abs(center - preceding.center)
            if not step < preceding.radius:
                raise ContinuationPlanError(
                    f"continuation path[{index}] is {step:g} from the preceding "
                    f"center; it must lie strictly inside that Taylor disc "
                    f"of radius {_format_radius(preceding.radius)}"
                )

        discs.append(ContinuationDisc(center=center, radius=radius))

    return tuple(discs)


def segment_interval_inside_disc(
    start: complex,
    end: complex,
    disc: ContinuationDisc,
) -> tuple[float, float] | None:
    """Return the portion of a line segment inside an open continuation disc."""

    if math.isinf(disc.radius):
        return (0.0, 1.0)

    radius = math.nextafter(disc.radius, 0.0)
    direction = end - start
    length = abs(direction)
    if length == 0:
        return (0.0, 1.0) if abs(start - disc.center) < radius else None
    if radius <= 0:
        return None

    center_offset = disc.center - start
    projection = (
        center_offset.real * direction.real
        + center_offset.imag * direction.imag
    ) / (length * length)
    perpendicular_distance = abs(
        center_offset.real * direction.imag
        - center_offset.imag * direction.real
    ) / length
    if perpendicular_distance >= radius:
        return None

    normalized_distance = perpendicular_distance / radius
    half_interval = (radius / length) * math.sqrt(
        max(0.0, 1.0 - normalized_distance * normalized_distance)
    )
    interval_start = max(0.0, projection - half_interval)
    interval_end = min(1.0, projection + half_interval)
    if interval_start >= interval_end:
        return None
    return (interval_start, interval_end)


def merge_intervals(
    intervals: Sequence[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    """Return the ordered geometric union of possibly overlapping intervals."""

    if not intervals:
        return ()

    ordered = sorted(intervals)
    merged: list[tuple[float, float]] = [ordered[0]]
    for interval_start, interval_end in ordered[1:]:
        preceding_start, preceding_end = merged[-1]
        if interval_start <= preceding_end:
            merged[-1] = (preceding_start, max(preceding_end, interval_end))
        else:
            merged.append((interval_start, interval_end))
    return tuple(merged)


def _format_complex(value: complex) -> str:
    if value.imag == 0:
        return f"{value.real:g}"
    return f"{value.real:g}{value.imag:+g}i"


def _format_radius(radius: float) -> str:
    return "infinity" if math.isinf(radius) else f"{radius:g}"
