from __future__ import annotations

import unittest

from analytic_continuation.spec import MovieSpecError, parse_movie_spec


class MovieSpecTests(unittest.TestCase):
    def test_defaults_are_small_and_reversible(self) -> None:
        movie = parse_movie_spec({"function": {"name": "exp"}})
        self.assertEqual(movie.view.center, 0j)
        self.assertEqual(movie.view.half_height, 4.0)
        self.assertEqual(movie.view.mode, "whole")
        self.assertIsNone(movie.view.continuation)
        self.assertTrue(movie.animation.close)

    def test_parses_continuation_view(self) -> None:
        movie = parse_movie_spec(
            {
                "function": {"name": "rational"},
                "view": {
                    "mode": "continuation",
                    "continuation": {
                        "path": [[2, 0], [2, 1]],
                        "patch_reveal_seconds": 0.4,
                    },
                },
            }
        )
        self.assertEqual(movie.view.mode, "continuation")
        self.assertIsNotNone(movie.view.continuation)
        assert movie.view.continuation is not None
        self.assertEqual(movie.view.continuation.path, (2 + 0j, 2 + 1j))
        self.assertEqual(movie.view.continuation.patch_reveal_seconds, 0.4)

    def test_continuation_path_must_not_be_empty(self) -> None:
        with self.assertRaisesRegex(MovieSpecError, "must not be empty"):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "view": {
                        "mode": "continuation",
                        "continuation": {
                            "path": [],
                            "patch_reveal_seconds": 0.4,
                        },
                    },
                }
            )

    def test_continuation_requires_explicit_patch_time(self) -> None:
        with self.assertRaisesRegex(MovieSpecError, "patch_reveal_seconds is required"):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "view": {
                        "mode": "continuation",
                        "continuation": {"path": [[0, 0]]},
                    },
                }
            )

    def test_continuation_patch_time_must_be_positive(self) -> None:
        with self.assertRaisesRegex(MovieSpecError, "must be greater than 0"):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "view": {
                        "mode": "continuation",
                        "continuation": {
                            "path": [[0, 0]],
                            "patch_reveal_seconds": 0,
                        },
                    },
                }
            )

    def test_continuation_mode_requires_settings(self) -> None:
        with self.assertRaisesRegex(MovieSpecError, "is required"):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "view": {"mode": "continuation"},
                }
            )

    def test_whole_view_rejects_ignored_continuation_settings(self) -> None:
        with self.assertRaisesRegex(MovieSpecError, "only allowed"):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "view": {
                        "continuation": {
                            "path": [[0, 0]],
                            "patch_reveal_seconds": 0.4,
                        }
                    },
                }
            )

    def test_probes_are_input_values(self) -> None:
        movie = parse_movie_spec(
            {
                "function": {"name": "sin"},
                "probes": [[1, 2], [-3, 4]],
            }
        )
        self.assertEqual(movie.probes, (1 + 2j, -3 + 4j))

    def test_rejects_nonpositive_view(self) -> None:
        with self.assertRaises(MovieSpecError):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "view": {"half_height": 0},
                }
            )

    def test_rejects_nonfinite_timing(self) -> None:
        with self.assertRaises(MovieSpecError):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "animation": {"open_seconds": float("nan")},
                }
            )

    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaises(MovieSpecError):
            parse_movie_spec(
                {
                    "function": {"name": "exp"},
                    "animaton": {},
                }
            )


if __name__ == "__main__":
    unittest.main()
