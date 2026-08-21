"""ManimGL scene selected by an ``ANALYTIC_CONTINUATION_SPEC`` file."""

from __future__ import annotations

import os

from manimlib import (  # type: ignore[import-not-found]
    BLUE_D,
    BLUE_E,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    GREY_B,
    UL,
    YELLOW,
    ComplexPlane,
    Dot,
    FadeIn,
    Scene,
    ShowCreation,
    Text,
    Transform,
    VGroup,
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
        coordinate_plane = ComplexPlane(
            x_range=(x_min, x_max, movie.view.grid_step),
            y_range=(y_min, y_max, movie.view.grid_step),
            width=FRAME_WIDTH - 0.35,
            height=FRAME_HEIGHT - 0.35,
            background_line_style={
                "stroke_color": BLUE_D,
                "stroke_width": 2,
                "stroke_opacity": 1,
            },
        )

        reference_plane = coordinate_plane.copy()
        reference_plane.set_stroke(GREY_B, width=1, opacity=0.28)

        moving_plane = coordinate_plane.copy()
        moving_plane.set_stroke(BLUE_E, width=1.5, opacity=0.92)
        moving_plane.prepare_for_nonlinear_transform(movie.animation.curve_density)
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

        self.add(reference_plane)
        opening_animations = [ShowCreation(moving_plane), FadeIn(title)]
        if len(probe_points) > 0:
            opening_animations.append(FadeIn(probe_points))
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
