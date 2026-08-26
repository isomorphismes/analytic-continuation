"""Command-line entry point for the renderer-independent reference model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .continuation import ContinuationPlanError, plan_continuation_discs
from .functions import FUNCTION_HELP, FunctionSpecError, make_complex_function
from .spec import MovieSpecError, load_movie_spec


def main(arguments: list[str] | None = None) -> int:
    parser = _parser()
    parsed = parser.parse_args(arguments)

    try:
        if parsed.command == "list-functions":
            for name, description in FUNCTION_HELP.items():
                print(f"{name:12} {description}")
            return 0

        specification_path = Path(parsed.specification).resolve()
        movie = load_movie_spec(specification_path)
        complex_function = make_complex_function(movie.function)
        if movie.view.disc_reveal is not None:
            plan_continuation_discs(
                complex_function,
                movie.view.disc_reveal.path,
            )

        if parsed.command == "validate":
            print(f"valid: {complex_function.label} — {complex_function.analytic_status}")
            return 0

    except (
        ContinuationPlanError,
        FunctionSpecError,
        MovieSpecError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    parser.error("missing command")
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analytic-continuation",
        description="Validate analytic-continuation reference specifications.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-functions", help="show the explicit function registry")

    validate = subparsers.add_parser(
        "validate",
        help="validate one visualization JSON file",
    )
    validate.add_argument("specification")

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
