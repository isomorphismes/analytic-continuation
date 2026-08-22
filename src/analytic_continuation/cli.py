"""Command-line entry point for validation and ManimGL rendering."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .functions import FUNCTION_HELP, FunctionSpecError, make_complex_function
from .spec import MovieSpecError, load_movie_spec

SPEC_ENVIRONMENT_VARIABLE = "ANALYTIC_CONTINUATION_SPEC"


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

        if parsed.command == "validate":
            print(f"valid: {complex_function.label} — {complex_function.analytic_status}")
            return 0

        if parsed.command == "render":
            command = render_command(specification_path, preview=parsed.preview)
            if parsed.dry_run:
                print(" ".join(command))
                return 0
            if shutil.which("manimgl") is None:
                raise RuntimeError(
                    "manimgl is not installed; install the movie extra with "
                    "pip install -e '.[movie]'"
                )
            environment = os.environ.copy()
            environment[SPEC_ENVIRONMENT_VARIABLE] = str(specification_path)
            return subprocess.run(command, env=environment, check=False).returncode
    except (FunctionSpecError, MovieSpecError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    parser.error("missing command")
    return 2


def render_command(specification_path: Path, preview: bool = False) -> list[str]:
    scene_path = Path(__file__).with_name("scene.py")
    command = ["manimgl", str(scene_path), "FunctionOpenClose"]
    if not preview:
        command.append("-w")
    return command


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analytic-continuation",
        description="Render an input complex grid opening into f(z) and closing again.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-functions", help="show the explicit function registry")

    validate = subparsers.add_parser("validate", help="validate one movie JSON file")
    validate.add_argument("specification")

    render = subparsers.add_parser("render", help="render one movie JSON file")
    render.add_argument("specification")
    render.add_argument(
        "--preview",
        action="store_true",
        help="open ManimGL interactively instead of writing a movie",
    )
    render.add_argument(
        "--dry-run",
        action="store_true",
        help="print the ManimGL command after validating the specification",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
