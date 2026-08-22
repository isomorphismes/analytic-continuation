"""Finite-dimensional completions for an underdetermined complex function.

A degree-N polynomial has N+1 complex coefficients.  If the user fixes the
value of the function at m distinct domain points, the remaining functions are

    interpolant(z) + product(z - z_i) * q(z),

where q has degree at most N-m.  That representation is useful for the visual
explorer because every added point removes exactly one complex degree of
freedom, while all previously fixed values remain exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from random import Random
from typing import Sequence


_DUPLICATE_POINT_TOLERANCE = 1.0e-9
_DIVISION_TOLERANCE = 1.0e-8


@dataclass(frozen=True)
class ValueConstraint:
    """One user-fixed value f(domain) = value."""

    domain: complex
    value: complex


def _trim(coefficients: Sequence[complex], tolerance: float = 1.0e-12) -> list[complex]:
    result = list(coefficients) or [0j]
    while len(result) > 1 and abs(result[-1]) <= tolerance:
        result.pop()
    return result


def _add(
    left: Sequence[complex],
    right: Sequence[complex],
) -> list[complex]:
    count = max(len(left), len(right))
    return _trim(
        [
            (left[index] if index < len(left) else 0j)
            + (right[index] if index < len(right) else 0j)
            for index in range(count)
        ]
    )


def _subtract(
    left: Sequence[complex],
    right: Sequence[complex],
) -> list[complex]:
    count = max(len(left), len(right))
    return _trim(
        [
            (left[index] if index < len(left) else 0j)
            - (right[index] if index < len(right) else 0j)
            for index in range(count)
        ]
    )


def _multiply(
    left: Sequence[complex],
    right: Sequence[complex],
) -> list[complex]:
    result = [0j] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            result[left_index + right_index] += left_value * right_value
    return _trim(result)


def _scale(
    coefficients: Sequence[complex],
    scalar: complex,
) -> list[complex]:
    return _trim([scalar * coefficient for coefficient in coefficients])


def evaluate_coefficients(coefficients: Sequence[complex], domain: complex) -> complex:
    """Evaluate ascending-power coefficients with Horner's rule."""

    value = 0j
    for coefficient in reversed(coefficients):
        value = value * domain + coefficient
    return value


def _interpolating_coefficients(
    constraints: Sequence[ValueConstraint],
) -> list[complex]:
    if not constraints:
        return [0j]

    result = [0j]
    for constraint_index, constraint in enumerate(constraints):
        basis = [1 + 0j]
        denominator = 1 + 0j
        for other_index, other in enumerate(constraints):
            if constraint_index == other_index:
                continue
            difference = constraint.domain - other.domain
            if abs(difference) <= _DUPLICATE_POINT_TOLERANCE:
                raise ValueError("constraint domain points must be distinct")
            basis = _multiply(basis, [-other.domain, 1 + 0j])
            denominator *= difference
        result = _add(result, _scale(basis, constraint.value / denominator))
    return result


def _vanishing_coefficients(
    constraints: Sequence[ValueConstraint],
) -> list[complex]:
    result = [1 + 0j]
    for constraint in constraints:
        result = _multiply(result, [-constraint.domain, 1 + 0j])
    return result


def _divide_exact(
    numerator: Sequence[complex],
    denominator: Sequence[complex],
) -> list[complex]:
    remainder = list(_trim(numerator))
    divisor = _trim(denominator)
    if abs(divisor[-1]) <= _DIVISION_TOLERANCE:
        raise ValueError("cannot divide by the zero polynomial")

    if len(remainder) < len(divisor):
        if max((abs(value) for value in remainder), default=0.0) > _DIVISION_TOLERANCE:
            raise ValueError("polynomial division left a nonzero remainder")
        return [0j]

    quotient = [0j] * (len(remainder) - len(divisor) + 1)
    while len(remainder) >= len(divisor):
        quotient_coefficient = remainder[-1] / divisor[-1]
        shift = len(remainder) - len(divisor)
        quotient[shift] = quotient_coefficient

        for index, divisor_coefficient in enumerate(divisor):
            remainder[index + shift] -= quotient_coefficient * divisor_coefficient
        remainder = _trim(remainder, _DIVISION_TOLERANCE)

    if max((abs(value) for value in remainder), default=0.0) > _DIVISION_TOLERANCE:
        raise ValueError("polynomial division left a nonzero remainder")
    return _trim(quotient)


def compose_coefficients(
    maximum_degree: int,
    constraints: Sequence[ValueConstraint],
    free_coefficients: Sequence[complex],
) -> tuple[complex, ...]:
    """Return one degree-bounded polynomial satisfying all constraints."""

    if maximum_degree < 0:
        raise ValueError("maximum_degree must be nonnegative")
    if len(constraints) > maximum_degree + 1:
        raise ValueError("too many constraints for the selected polynomial degree")

    interpolant = _interpolating_coefficients(constraints)
    vanishing = _vanishing_coefficients(constraints)
    free_count = maximum_degree + 1 - len(constraints)
    free = list(free_coefficients[:free_count])
    free.extend([0j] * (free_count - len(free)))

    result = _add(interpolant, _multiply(vanishing, free))
    result.extend([0j] * (maximum_degree + 1 - len(result)))
    return tuple(result[: maximum_degree + 1])


class UnderdeterminedPolynomialFamily:
    """A bounded random walk through all still-allowed polynomial completions."""

    def __init__(
        self,
        maximum_degree: int = 7,
        *,
        random_seed: int = 0,
        wander_scale: float = 0.018,
        restoring_strength: float = 0.002,
    ) -> None:
        if maximum_degree < 0:
            raise ValueError("maximum_degree must be nonnegative")
        if wander_scale < 0.0:
            raise ValueError("wander_scale must be nonnegative")
        if restoring_strength < 0.0 or restoring_strength > 1.0:
            raise ValueError("restoring_strength must be between zero and one")

        self.maximum_degree = maximum_degree
        self.wander_scale = wander_scale
        self.restoring_strength = restoring_strength
        self._random = Random(random_seed)
        self._constraints: list[ValueConstraint] = []
        self._free_coefficients = [
            self._random_complex(0.22) for _ in range(maximum_degree + 1)
        ]
        self._free_coefficients[0] += 1.0 + 0j

    @property
    def constraints(self) -> tuple[ValueConstraint, ...]:
        return tuple(self._constraints)

    @property
    def remaining_complex_dimensions(self) -> int:
        return self.maximum_degree + 1 - len(self._constraints)

    @property
    def freedom_fraction(self) -> float:
        return self.remaining_complex_dimensions / (self.maximum_degree + 1)

    @property
    def coefficients(self) -> tuple[complex, ...]:
        return compose_coefficients(
            self.maximum_degree,
            self._constraints,
            self._free_coefficients,
        )

    def evaluate(self, domain: complex) -> complex:
        return evaluate_coefficients(self.coefficients, domain)

    def lock_current_value(self, domain: complex) -> ValueConstraint:
        """Freeze the current value at ``domain`` without changing this frame."""

        if self.remaining_complex_dimensions == 0:
            raise ValueError("the polynomial family is already fully determined")
        for constraint in self._constraints:
            if abs(domain - constraint.domain) <= _DUPLICATE_POINT_TOLERANCE:
                raise ValueError("that domain point is already constrained")

        current_coefficients = self.coefficients
        constraint = ValueConstraint(
            domain=domain,
            value=evaluate_coefficients(current_coefficients, domain),
        )
        new_constraints = [*self._constraints, constraint]

        interpolant = _interpolating_coefficients(new_constraints)
        vanishing = _vanishing_coefficients(new_constraints)
        residual = _subtract(current_coefficients, interpolant)
        new_free = _divide_exact(residual, vanishing)
        needed = self.maximum_degree + 1 - len(new_constraints)
        new_free.extend([0j] * (needed - len(new_free)))

        self._constraints = new_constraints
        self._free_coefficients = new_free[:needed]
        return constraint

    def step(self, frame_fraction: float = 1.0) -> bool:
        """Advance the random walk; return whether the function can still move."""

        free_count = self.remaining_complex_dimensions
        if free_count == 0:
            return False
        if frame_fraction < 0.0:
            raise ValueError("frame_fraction must be nonnegative")
        if frame_fraction == 0.0:
            return True

        freedom_scale = sqrt(self.freedom_fraction)
        noise_scale = self.wander_scale * freedom_scale * sqrt(frame_fraction)
        restoring = min(1.0, self.restoring_strength * frame_fraction)

        for index in range(free_count):
            coefficient = self._free_coefficients[index]
            coefficient *= 1.0 - restoring
            coefficient += self._random_complex(noise_scale)
            self._free_coefficients[index] = coefficient
        return True

    def _random_complex(self, scale: float) -> complex:
        return complex(
            self._random.gauss(0.0, scale),
            self._random.gauss(0.0, scale),
        )
