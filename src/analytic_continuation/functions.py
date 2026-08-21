"""A deliberately small registry of complex functions.

There is no ``eval`` entry point.  Adding a function means giving it an
explicit name, parameter contract, evaluator, and mathematical status.
"""

from __future__ import annotations

import cmath
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .complex_values import ComplexValueError, parse_complex

ComplexEvaluator = Callable[[complex], complex]


class FunctionSpecError(ValueError):
    """Raised when a function specification is unknown or malformed."""


@dataclass(frozen=True)
class ComplexFunction:
    name: str
    label: str
    evaluate: ComplexEvaluator
    analytic_status: str
    poles: tuple[complex, ...] = ()
    branch_points: tuple[complex, ...] = ()
    zeros: tuple[complex, ...] = ()
    finite_singularities_complete: bool = False


FUNCTION_HELP: dict[str, str] = {
    "exp": "entire exponential",
    "sin": "entire sine",
    "polynomial": "polynomial with coefficients in ascending powers",
    "rational": "nonzero gain times zero factors divided by pole factors",
    "zeta": "Riemann zeta, meromorphic with one pole at 1",
    "gamma": "gamma, meromorphic with poles at 0, -1, -2, ...",
    "airy_ai": "Airy Ai, entire",
    "airy_bi": "Airy Bi, entire",
    "bessel_j": "Bessel J of a chosen order; integer orders are entire",
}


def available_function_names() -> tuple[str, ...]:
    return tuple(FUNCTION_HELP)


def make_complex_function(specification: Mapping[str, Any]) -> ComplexFunction:
    """Build a callable complex function from a validated registry entry."""

    if not isinstance(specification, Mapping):
        raise FunctionSpecError("function must be an object")

    unknown = set(specification) - {"name", "parameters"}
    if unknown:
        raise FunctionSpecError(_unknown_fields("function", unknown))

    name = specification.get("name")
    if not isinstance(name, str) or not name:
        raise FunctionSpecError("function.name must be a non-empty string")
    if name not in FUNCTION_HELP:
        available = ", ".join(available_function_names())
        raise FunctionSpecError(f"unknown function {name!r}; available functions: {available}")

    parameters = specification.get("parameters", {})
    if not isinstance(parameters, Mapping):
        raise FunctionSpecError("function.parameters must be an object")

    builders: dict[str, Callable[[Mapping[str, Any]], ComplexFunction]] = {
        "exp": _make_exp,
        "sin": _make_sin,
        "polynomial": _make_polynomial,
        "rational": _make_rational,
        "zeta": _make_zeta,
        "gamma": _make_gamma,
        "airy_ai": _make_airy_ai,
        "airy_bi": _make_airy_bi,
        "bessel_j": _make_bessel_j,
    }
    return builders[name](parameters)


def _make_exp(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_no_parameters("exp", parameters)
    return ComplexFunction(
        "exp",
        "exp(z)",
        cmath.exp,
        "entire",
        finite_singularities_complete=True,
    )


def _make_sin(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_no_parameters("sin", parameters)
    return ComplexFunction(
        "sin",
        "sin(z)",
        cmath.sin,
        "entire",
        finite_singularities_complete=True,
    )


def _make_polynomial(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_only("polynomial", parameters, {"coefficients"})
    raw_coefficients = parameters.get("coefficients")
    if not isinstance(raw_coefficients, Sequence) or isinstance(
        raw_coefficients, (str, bytes, bytearray)
    ):
        raise FunctionSpecError("polynomial.parameters.coefficients must be a list")
    if not raw_coefficients:
        raise FunctionSpecError("polynomial.parameters.coefficients must not be empty")

    try:
        coefficients = tuple(
            parse_complex(value, f"polynomial.parameters.coefficients[{index}]")
            for index, value in enumerate(raw_coefficients)
        )
    except ComplexValueError as error:
        raise FunctionSpecError(str(error)) from error

    def evaluate(value: complex) -> complex:
        result = 0j
        for coefficient in reversed(coefficients):
            result = result * value + coefficient
        return result

    degree = len(coefficients) - 1
    return ComplexFunction(
        "polynomial",
        f"polynomial of degree {degree}",
        evaluate,
        "entire",
        finite_singularities_complete=True,
    )


def _make_rational(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_only("rational", parameters, {"gain", "zeros", "poles"})

    try:
        gain = parse_complex(parameters.get("gain", 1.0), "rational.parameters.gain")
        zeros = _parse_complex_list(parameters.get("zeros", []), "rational.parameters.zeros")
        poles = _parse_complex_list(parameters.get("poles", []), "rational.parameters.poles")
    except ComplexValueError as error:
        raise FunctionSpecError(str(error)) from error

    if gain == 0:
        raise FunctionSpecError(
            "rational.parameters.gain must be nonzero; zero gain would collapse "
            "the factor model and make every listed pole removable"
        )

    zeros, poles = _cancel_shared_factors(zeros, poles)

    def evaluate(value: complex) -> complex:
        numerator = gain
        denominator = 1 + 0j
        for zero in zeros:
            numerator *= value - zero
        for pole in poles:
            denominator *= value - pole
        return numerator / denominator

    if poles:
        status = "meromorphic rational function"
    else:
        status = "entire polynomial in zero-factor form"
    return ComplexFunction(
        "rational",
        _rational_label(zeros, poles, gain),
        evaluate,
        status,
        zeros=zeros,
        poles=poles,
        finite_singularities_complete=True,
    )


def _make_zeta(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_no_parameters("zeta", parameters)
    mp = _load_mpmath()
    return ComplexFunction(
        "zeta",
        "ζ(z)",
        lambda value: complex(mp.zeta(value)),
        "meromorphic continuation to the plane, with a simple pole at 1",
        poles=(1 + 0j,),
        finite_singularities_complete=True,
    )


def _make_gamma(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_no_parameters("gamma", parameters)
    mp = _load_mpmath()
    return ComplexFunction(
        "gamma",
        "Γ(z)",
        lambda value: complex(mp.gamma(value)),
        "meromorphic, with simple poles at the non-positive integers",
        finite_singularities_complete=False,
    )


def _make_airy_ai(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_no_parameters("airy_ai", parameters)
    mp = _load_mpmath()
    return ComplexFunction(
        "airy_ai",
        "Ai(z)",
        lambda value: complex(mp.airyai(value)),
        "entire",
        finite_singularities_complete=True,
    )


def _make_airy_bi(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_no_parameters("airy_bi", parameters)
    mp = _load_mpmath()
    return ComplexFunction(
        "airy_bi",
        "Bi(z)",
        lambda value: complex(mp.airybi(value)),
        "entire",
        finite_singularities_complete=True,
    )


def _make_bessel_j(parameters: Mapping[str, Any]) -> ComplexFunction:
    _require_only("bessel_j", parameters, {"order"})
    try:
        order = parse_complex(parameters.get("order", 0.0), "bessel_j.parameters.order")
    except ComplexValueError as error:
        raise FunctionSpecError(str(error)) from error

    mp = _load_mpmath()
    integral_order = order.imag == 0.0 and order.real.is_integer()
    if integral_order:
        status = "entire in z for integer order"
        branch_points: tuple[complex, ...] = ()
        order_label = str(int(order.real))
    else:
        status = "principal branch; branch point at 0 for non-integer order"
        branch_points = (0j,)
        order_label = _format_complex(order)

    return ComplexFunction(
        "bessel_j",
        f"J_{order_label}(z)",
        lambda value: complex(mp.besselj(order, value)),
        status,
        branch_points=branch_points,
        finite_singularities_complete=integral_order,
    )


def _parse_complex_list(raw_values: Any, field_name: str) -> tuple[complex, ...]:
    if not isinstance(raw_values, Sequence) or isinstance(
        raw_values, (str, bytes, bytearray)
    ):
        raise ComplexValueError(f"{field_name} must be a list")
    return tuple(
        parse_complex(value, f"{field_name}[{index}]")
        for index, value in enumerate(raw_values)
    )


def _cancel_shared_factors(
    zeros: tuple[complex, ...],
    poles: tuple[complex, ...],
) -> tuple[tuple[complex, ...], tuple[complex, ...]]:
    """Cancel exact shared factors one-for-one while preserving input order."""

    cancellations = Counter(zeros) & Counter(poles)

    def without_cancelled(
        values: tuple[complex, ...],
    ) -> tuple[complex, ...]:
        remaining_cancellations = cancellations.copy()
        result: list[complex] = []
        for value in values:
            if remaining_cancellations[value] > 0:
                remaining_cancellations[value] -= 1
            else:
                result.append(value)
        return tuple(result)

    return without_cancelled(zeros), without_cancelled(poles)


def _rational_label(zeros: tuple[complex, ...], poles: tuple[complex, ...], gain: complex) -> str:
    pieces = []
    if gain != 1:
        pieces.append(_format_complex(gain))
    pieces.append(f"{len(zeros)} zero factor{'s' if len(zeros) != 1 else ''}")
    if poles:
        pieces.append(f"{len(poles)} pole factor{'s' if len(poles) != 1 else ''}")
    return "; ".join(pieces)


def _format_complex(value: complex) -> str:
    if value.imag == 0:
        return f"{value.real:g}"
    return f"{value.real:g}{value.imag:+g}i"


def _load_mpmath():
    try:
        import mpmath  # type: ignore[import-not-found]
    except ModuleNotFoundError as error:
        raise FunctionSpecError(
            "mpmath is required for zeta, gamma, Airy, and Bessel functions; "
            "install the project dependencies"
        ) from error
    return mpmath


def _require_no_parameters(function_name: str, parameters: Mapping[str, Any]) -> None:
    _require_only(function_name, parameters, set())


def _require_only(
    function_name: str,
    parameters: Mapping[str, Any],
    allowed: set[str],
) -> None:
    unknown = set(parameters) - allowed
    if unknown:
        raise FunctionSpecError(_unknown_fields(f"{function_name}.parameters", unknown))


def _unknown_fields(place: str, fields: set[Any]) -> str:
    names = ", ".join(sorted(str(name) for name in fields))
    return f"{place} has unknown fields: {names}"
