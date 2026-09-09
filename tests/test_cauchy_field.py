from __future__ import annotations

import math
import unittest


SOURCE_COUNT = 24
TAU = 2.0 * math.pi


def fract(value: float) -> float:
    return value - math.floor(value)


def hash1(value: float) -> float:
    return fract(math.sin(value * 127.1) * 43758.5453123)


def source_position(index: int, time: float, view_radius: float) -> complex:
    source_index = float(index)
    theta0 = TAU * hash1(source_index + 0.13)
    omega = 0.10 + (0.55 - 0.10) * hash1(source_index + 1.91)
    wobble = 0.05 + (0.25 - 0.05) * hash1(source_index + 7.12)
    theta = theta0 + omega * time + 0.20 * math.sin(
        wobble * time + TAU * hash1(source_index + 3.77)
    )

    radial_omega = 0.07 + (0.31 - 0.07) * hash1(source_index + 5.44)
    radius = 1.8 * view_radius + 0.35 * view_radius * math.sin(
        radial_omega * time + TAU * hash1(source_index + 9.61)
    )
    return radius * complex(math.cos(theta), math.sin(theta))


def source_weight(index: int, time: float) -> complex:
    source_index = float(index)
    amplitude = 0.08 + (0.35 - 0.08) * hash1(source_index + 11.3)
    omega = 0.08 + (0.60 - 0.08) * hash1(source_index + 17.8)
    phi = TAU * hash1(source_index + 21.4) + omega * time
    return amplitude * complex(math.cos(phi), math.sin(phi))


def cauchy_field(z: complex, time: float, view_radius: float) -> complex:
    return sum(
        source_weight(index, time) / (source_position(index, time, view_radius) - z)
        for index in range(SOURCE_COUNT)
    )


class CauchyFieldTests(unittest.TestCase):
    def test_sources_stay_outside_the_visible_disk(self) -> None:
        view_radius = 3.0
        for time in (0.0, 4.0, 17.0, 60.0, 120.0):
            for index in range(SOURCE_COUNT):
                with self.subTest(time=time, index=index):
                    self.assertGreater(
                        abs(source_position(index, time, view_radius)),
                        view_radius,
                    )

    def test_field_motion_is_independent_of_the_divisor(self) -> None:
        # This test evaluates q_t directly. It intentionally has no zero/pole
        # inputs, so repeated roots in R cannot make genuine Cauchy-field motion
        # disappear from the acceptance signal.
        width = 1080.0
        height = 2400.0
        pixel_radius = 0.42 * min(width, height)
        view_radius = math.hypot(0.5 * width, 0.5 * height) / pixel_radius
        sample_points = [
            complex(x * 0.30, y * 0.60)
            for y in range(-3, 4)
            for x in range(-3, 4)
        ]
        sample_points = [point for point in sample_points if abs(point) <= view_radius]

        for start_time in (0.0, 4.0, 17.0, 60.0):
            deltas = [
                abs(
                    cauchy_field(point, start_time + 6.0, view_radius)
                    - cauchy_field(point, start_time, view_radius)
                )
                for point in sample_points
            ]
            mean_delta = sum(deltas) / len(deltas)
            with self.subTest(start_time=start_time):
                self.assertGreater(mean_delta, 0.04)


if __name__ == "__main__":
    unittest.main()
