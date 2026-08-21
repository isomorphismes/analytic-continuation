"""Small, strict helpers for complex values stored in JSON."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


class ComplexValueError(ValueError):
    """Raised when JSON does not contain an unambiguous complex value."""


def parse_complex(value: Any, field_name: str) -> complex:
    """Parse a real number, ``[real, imag]``, or ``{"real": ..., "imag": ...}``.

    Strings are deliberately rejected.  Accepting strings would require an
    expression language and would make a misspelling look like a valid value.
    """

    if isinstance(value, bool):
        raise ComplexValueError(f"{field_name} must be a complex value, not a boolean")

    if isinstance(value, (int, float)):
        return complex(_parse_real(value, field_name), 0.0)

    if isinstance(value, Mapping):
        unknown = set(value) - {"real", "imag"}
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise ComplexValueError(f"{field_name} has unknown fields: {names}")
        if "real" not in value:
            raise ComplexValueError(f"{field_name}.real is required")
        real = _parse_real(value["real"], f"{field_name}.real")
        imag = _parse_real(value.get("imag", 0.0), f"{field_name}.imag")
        return complex(real, imag)

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) != 2:
            raise ComplexValueError(f"{field_name} must contain [real, imag]")
        real = _parse_real(value[0], f"{field_name}[0]")
        imag = _parse_real(value[1], f"{field_name}[1]")
        return complex(real, imag)

    raise ComplexValueError(
        f"{field_name} must be a number, [real, imag], or an object with real/imag"
    )


def complex_to_pair(value: complex) -> list[float]:
    """Return a JSON-compatible ``[real, imag]`` pair."""

    return [float(value.real), float(value.imag)]


def _parse_real(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComplexValueError(f"{field_name} must be a real number")
    try:
        number = float(value)
    except OverflowError as error:
        raise ComplexValueError(f"{field_name} must be finite") from error
    if not math.isfinite(number):
        raise ComplexValueError(f"{field_name} must be finite")
    return number
