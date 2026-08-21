"""ManimGL scene selected by an ``ANALYTIC_CONTINUATION_SPEC`` file."""

from __future__ import annotations

import math
import os
from collections import Counter

from manimlib import (  # type: ignore[import-not-found]
    BLUE_D,
    BLUE_E,
    DOWN,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    GREEN,
    GREY_B,
    RED,
    UL,
    YELLOW,
    Circle,
    ComplexPlane,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    Scene,
    ShowCreation,
    Text,
    Transform,
    VGroup,
)

from analytic_continuation.continuation import (
    ContinuationDisc,
    merge_intervals,
    plan_continuation_discs,
    segment_interval_inside_disc,
)
from analytic_continuation.functions import make_complex_function
from analytic_continuation.mapping import ViewBox, make_visible_map
from analytic_continuation.spec import load_movie_spec

SPEC_ENVIRONMENT_VARIABLE = "ANALYTIC_CONTINUATION_SPEC"


class FunctionOpenClose(Scene):
    """Deform a complex grid under f, pause, and restore the input grid."""

    def construct(self) -> None:
        specification_path = os.environ.get(SPEC_ENVIRONMENT_VARIABLE)
        if not specification_path:
            raise RuntimeError(
                f"{SPEC_ENVIRONMENT_VARIABLE} must name a movie JSON file"
            )

        movie = load_movie_spec(specification_path)
        complex_function = make_complex_function(movie.function)
        continuation_discs: tuple[ContinuationDisc, ...] = ()
        if movie.view.disc_reveal is not None:
            continuation_discs = plan_continuation_discs(
                complex_function,
                movie.view.disc_reveal.path,
            )

        half_width = movie.view.half_height * FRAME_WIDTH / FRAME_HEIGHT
        view_box = ViewBox(
            center=movie.view.center,
            half_width=half_width,
            half_height=movie.view.half_height,
            margin=movie.animation.output_margin,
        )
        visible_map = make_visible_map(complex_function.evaluate, view_box)

        x_min = movie.view.center.real - half_width
        x_max = movie.view.center.real + half_width
        y_min = movie.view.center.imag - movie.view.half_height
        y_max = movie.view.center.imag + movie.view.half_height
        plane_height = FRAME_HEIGHT - 0.35
        plane_width = plane_height * FRAME_WIDTH / FRAME_HEIGHT
        coordinate_plane = ComplexPlane(
            x_range=(x_min, x_max, movie.view.grid_step),
            y_range=(y_min, y_max, movie.view.grid_step),
            width=plane_width,
            height=plane_height,
            background_line_style={
                "stroke_color": BLUE_D,
                "stroke_width": 2,
                "stroke_opacity": 1,
            },
        )
        input_factor_markers = _make_factor_markers(
            coordinate_plane,
            complex_function.zeros,
            complex_function.poles,
        )

        revealed_grid: VGroup | None = None
        if movie.view.disc_reveal is not None:
            if len(input_factor_markers) > 0:
                self.play(
                    FadeIn(input_factor_markers),
                    run_time=min(
                        0.5,
                        movie.view.disc_reveal.patch_reveal_seconds,
                    ),
                )
            revealed_grid = self._reveal_disc_patches(
                coordinate_plane=coordinate_plane,
                discs=continuation_discs,
                patch_reveal_seconds=movie.view.disc_reveal.patch_reveal_seconds,
                foreground_markers=input_factor_markers,
            )

        if revealed_grid is None:
            moving_plane = coordinate_plane.copy()
        else:
            moving_plane = revealed_grid
        reference_plane = moving_plane.copy()
        reference_plane.set_stroke(GREY_B, width=1, opacity=0.28)

        moving_plane.set_stroke(BLUE_E, width=1.5, opacity=0.92)
        _prepare_for_nonlinear_transform(
            moving_plane,
            movie.animation.curve_density,
        )
        original_plane = moving_plane.copy()
        transformed_plane = moving_plane.copy()
        transformed_plane.apply_function(
            lambda point: coordinate_plane.n2p(
                visible_map(coordinate_plane.p2n(point))
            )
        )

        probe_points = VGroup(
            *(Dot(coordinate_plane.n2p(value), color=YELLOW) for value in movie.probes)
        )
        original_probe_points = probe_points.copy()
        transformed_probe_points = VGroup(
            *(
                Dot(coordinate_plane.n2p(visible_map(value)), color=YELLOW)
                for value in movie.probes
            )
        )
        title_text = movie.title or complex_function.label
        title = Text(title_text, font_size=36)
        title.to_corner(UL)
        title.set_backstroke(width=7)

        if revealed_grid is None:
            self.add(reference_plane)
            opening_animations = [ShowCreation(moving_plane), FadeIn(title)]
        else:
            self.add(reference_plane, moving_plane, input_factor_markers)
            opening_animations = [FadeIn(title)]
        if len(probe_points) > 0:
            opening_animations.append(FadeIn(probe_points))
        if revealed_grid is None and len(input_factor_markers) > 0:
            opening_animations.append(FadeIn(input_factor_markers))
        self.play(*opening_animations, run_time=1.25)

        transform_animations = [Transform(moving_plane, transformed_plane)]
        if len(probe_points) > 0:
            transform_animations.append(Transform(probe_points, transformed_probe_points))
        self.play(*transform_animations, run_time=movie.animation.open_seconds)
        self.wait(movie.animation.hold_seconds)

        if movie.animation.close:
            closing_animations = [Transform(moving_plane, original_plane)]
            if len(probe_points) > 0:
                closing_animations.append(Transform(probe_points, original_probe_points))
            self.play(*closing_animations, run_time=movie.animation.close_seconds)

    def _reveal_disc_patches(
        self,
        coordinate_plane: ComplexPlane,
        discs: tuple[ContinuationDisc, ...],
        patch_reveal_seconds: float,
        foreground_markers: VGroup,
    ) -> VGroup:
        disclosure = Text(
            "Disc reveal only — values use the selected closed form",
            font_size=22,
        )
        disclosure.to_edge(DOWN)
        disclosure.set_backstroke(width=6)
        self.play(FadeIn(disclosure), run_time=min(0.5, patch_reveal_seconds))

        revealed_patches = VGroup()
        revealed_marks = VGroup()
        for disc in discs:
            grid_patch, disc_marks = _make_continuation_patch(
                coordinate_plane=coordinate_plane,
                disc=disc,
            )
            animations = [FadeIn(grid_patch)]
            if len(disc_marks) > 0:
                animations.append(ShowCreation(disc_marks))
            self.play(*animations, run_time=patch_reveal_seconds)
            revealed_patches.add(grid_patch)
            revealed_marks.add(disc_marks)
            self.add(foreground_markers)

        self.remove(*revealed_marks)
        self.add(revealed_marks)
        self.play(
            FadeOut(revealed_marks),
            FadeOut(disclosure),
            run_time=min(0.5, patch_reveal_seconds),
        )
        self.remove(*revealed_patches)
        union_grid = _make_continuation_union(coordinate_plane, discs)
        self.add(union_grid, foreground_markers)
        return union_grid


def _make_continuation_patch(
    coordinate_plane: ComplexPlane,
    disc: ContinuationDisc,
) -> tuple[VGroup, VGroup]:
    """Clip the actual plane lattice to one pole-free Taylor disc."""

    grid_patch = VGroup()
    for source_line in coordinate_plane.family_members_with_points():
        start = coordinate_plane.p2n(source_line.get_start())
        end = coordinate_plane.p2n(source_line.get_end())
        direction = end - start
        tolerance = 1.0e-9 * max(1.0, abs(direction))
        if abs(direction.real) > tolerance and abs(direction.imag) > tolerance:
            continue

        interval = segment_interval_inside_disc(start, end, disc)
        if interval is None:
            continue
        clipped_line = source_line.copy()
        clipped_line.pointwise_become_partial(source_line, *interval)
        grid_patch.add(clipped_line)

    disc_marks = VGroup()
    screen_center = coordinate_plane.n2p(disc.center)
    if math.isfinite(disc.radius):
        screen_edge = coordinate_plane.n2p(disc.center + disc.radius)
        screen_radius = math.hypot(
            float(screen_edge[0] - screen_center[0]),
            float(screen_edge[1] - screen_center[1]),
        )
        outline = Circle(radius=screen_radius)
        outline.move_to(screen_center)
        outline.set_stroke(YELLOW, width=2, opacity=0.85)
        disc_marks.add(outline)
    disc_marks.add(Dot(screen_center, radius=0.045, color=YELLOW))
    return grid_patch, disc_marks


def _make_continuation_union(
    coordinate_plane: ComplexPlane,
    discs: tuple[ContinuationDisc, ...],
) -> VGroup:
    """Merge overlapping disc coverage once for every actual plane line."""

    union_grid = VGroup()
    for source_line in coordinate_plane.family_members_with_points():
        start = coordinate_plane.p2n(source_line.get_start())
        end = coordinate_plane.p2n(source_line.get_end())
        direction = end - start
        tolerance = 1.0e-9 * max(1.0, abs(direction))
        if abs(direction.real) > tolerance and abs(direction.imag) > tolerance:
            continue

        intervals = tuple(
            interval
            for disc in discs
            if (interval := segment_interval_inside_disc(start, end, disc))
            is not None
        )
        for interval in merge_intervals(intervals):
            clipped_line = source_line.copy()
            clipped_line.pointwise_become_partial(source_line, *interval)
            union_grid.add(clipped_line)
    return union_grid


def _prepare_for_nonlinear_transform(
    grid: ComplexPlane | VGroup,
    curve_density: int,
) -> None:
    """Densify either the whole plane or a continuation patch union."""

    for member in grid.family_members_with_points():
        number_of_curves = member.get_num_curves()
        if curve_density > number_of_curves:
            member.insert_n_curves(curve_density - number_of_curves)
        member.make_smooth_after_applying_functions = True


def _make_factor_markers(
    coordinate_plane: ComplexPlane,
    zeros: tuple[complex, ...],
    poles: tuple[complex, ...],
) -> VGroup:
    """Make multiplicity-aware input markers: rings for zeros, crosses for poles."""

    markers = VGroup()
    for value, multiplicity in Counter(zeros).items():
        screen_point = coordinate_plane.n2p(value)
        for index in range(multiplicity):
            ring = Circle(radius=0.08 + 0.035 * index)
            ring.move_to(screen_point)
            ring.set_fill(opacity=0)
            ring.set_stroke(GREEN, width=3)
            markers.add(ring)

    for value, multiplicity in Counter(poles).items():
        screen_point = coordinate_plane.n2p(value)
        for index in range(multiplicity):
            half_size = 0.08 + 0.035 * index
            cross = VGroup(
                Line(
                    [-half_size, -half_size, 0],
                    [half_size, half_size, 0],
                ),
                Line(
                    [-half_size, half_size, 0],
                    [half_size, -half_size, 0],
                ),
            )
            cross.move_to(screen_point)
            cross.set_stroke(RED, width=3)
            markers.add(cross)
    return markers
