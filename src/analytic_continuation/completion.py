"""Transcendental analytic completions for an underdetermined complex function.

The displayed function is

    f(z) = A(z) + V(z) W(z)

where V(z) is the product of (z - z_i) over every user-constrained domain
point, A(z) is an analytic anchor, and W(z) is a small random sum of complex
exponentials.  V makes every future perturbation vanish at every constrained
point.  Adding a constraint folds the current V W term into A first, so locking
the current value does not change the displayed frame.

The exponential modes make the family non-polynomial.  Constraints damp the
walk but do not consume a finite list of mathematical degrees of freedom.
The finite mode and constraint counts are rendering/storage budgets only.
"""

from __future__ import annotations

from cmath import exp
from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from random import Random


_DUPLICATE_POINT_TOLERANCE = 1.0e-9
_DIVISION_TOLERANCE = 1.0e-12
_DEFAULT_MODE_COUNT = 4
_DEFAULT_CONSTRAINT_CAPACITY = 12


@dataclass(frozen=True)
class ValueConstraint:
    """One user-fixed value f(domain) = value."""

    domain: complex
    value: complex


def _evaluate_polynomial(coefficients: list[complex], domain: complex) -> complex:
    value = 0j
    for coefficient in reversed(coefficients):
        value = value * domain + coefficient
    return value


def _vanishing_coefficients(constraints: tuple[ValueConstraint, ...]) -> list[complex]:
    coefficients = [1 + 0j]
    for constraint in constraints:
        next_coefficients = [0j] * (len(coefficients) + 1)
        for index, coefficient in enumerate(coefficients):
            next_coefficients[index] -= constraint.domain * coefficient
            next_coefficients[index + 1] += coefficient
        coefficients = next_coefficients
    return coefficients


def _evaluate_vanishing(constraints: tuple[ValueConstraint, ...], domain: complex) -> complex:
    value = 1 + 0j
    for constraint in constraints:
        value *= domain - constraint.domain
    return value


class UnderdeterminedAnalyticFamily:
    """A damped random walk through non-polynomial analytic completions."""

    def __init__(
        self,
        *,
        random_seed: int = 0,
        mode_count: int = _DEFAULT_MODE_COUNT,
        constraint_capacity: int = _DEFAULT_CONSTRAINT_CAPACITY,
        wander_scale: float = 0.0085,
    ) -> None:
        if mode_count < 2:
            raise ValueError("mode_count must include a constant mode and a transcendental mode")
        if constraint_capacity < 1:
            raise ValueError("constraint_capacity must be positive")
        if wander_scale < 0.0:
            raise ValueError("wander_scale must be nonnegative")

        self.constraint_capacity = constraint_capacity
        self.wander_scale = wander_scale
        self._random = Random(random_seed)
        self._constraints: list[ValueConstraint] = []
        self._mode_frequencies = [0j]
        for _ in range(1, mode_count):
            angle = 2.0 * pi * self._random.random()
            magnitude = 0.055 + 0.035 * self._random.random()
            self._mode_frequencies.append(
                magnitude * complex(cos(angle), sin(angle))
            )

        self._anchor_polynomials = [
            [0j] * (constraint_capacity + 1) for _ in range(mode_count)
        ]
        self._anchor_polynomials[0][0] = 0.55 + 0.15j
        self._anchor_polynomials[0][1] = 0.90 + 0.05j
        self._anchor_polynomials[0][2] = 0.08 - 0.06j
        for mode in range(1, mode_count):
            scale = 0.075 / mode
            self._anchor_polynomials[mode][0] = self._random_complex(scale)

        self._wander = [0j] * mode_count

    @property
    def constraints(self) -> tuple[ValueConstraint, ...]:
        return tuple(self._constraints)

    @property
    def mode_frequencies(self) -> tuple[complex, ...]:
        return tuple(self._mode_frequencies)

    @property
    def constraint_slots_remaining(self) -> int:
        return self.constraint_capacity - len(self._constraints)

    @property
    def motion_scale(self) -> float:
        return 1.0 / sqrt(1.0 + 0.55 * len(self._constraints))

    @property
    def is_transcendental(self) -> bool:
        return any(
            abs(frequency) > 0.0
            and any(abs(coefficient) > 0.0 for coefficient in polynomial)
            for frequency, polynomial in zip(
                self._mode_frequencies[1:],
                self._anchor_polynomials[1:],
            )
        )

    def evaluate(self, domain: complex) -> complex:
        anchor = 0j
        wander_sum = 0j
        for frequency, polynomial, wander in zip(
            self._mode_frequencies,
            self._anchor_polynomials,
            self._wander,
        ):
            exponential = exp(frequency * domain)
            anchor += _evaluate_polynomial(polynomial, domain) * exponential
            wander_sum += wander * exponential

        return anchor + _evaluate_vanishing(self.constraints, domain) * wander_sum

    def constrain_value(self, domain: complex, value: complex) -> ValueConstraint:
        if self.constraint_slots_remaining <= 0:
            raise ValueError("constraint storage is full")
        if any(
            abs(domain - constraint.domain) <= _DUPLICATE_POINT_TOLERANCE
            for constraint in self._constraints
        ):
            raise ValueError("that domain point is already constrained")

        current_value = self.evaluate(domain)
        old_constraints = self.constraints
        response = _evaluate_vanishing(old_constraints, domain)
        if abs(response) <= _DIVISION_TOLERANCE:
            raise ValueError("that domain point is already constrained")

        self._commit_wander(old_constraints)
        correction_scale = (value - current_value) / response
        vanishing_coefficients = _vanishing_coefficients(old_constraints)
        for index, coefficient in enumerate(vanishing_coefficients):
            self._anchor_polynomials[0][index] += correction_scale * coefficient

        constraint = ValueConstraint(domain=domain, value=value)
        self._constraints.append(constraint)
        return constraint

    def lock_current_value(self, domain: complex) -> ValueConstraint:
        """Freeze the current value at domain without changing this frame."""

        return self.constrain_value(domain, self.evaluate(domain))

    def step(self, frame_fraction: float = 1.0) -> bool:
        if frame_fraction < 0.0:
            raise ValueError("frame_fraction must be nonnegative")
        if frame_fraction == 0.0:
            return True

        damping = 0.985**frame_fraction
        noise_scale = self.wander_scale * self.motion_scale * sqrt(frame_fraction)
        for mode in range(len(self._wander)):
            mode_scale = 1.0 / sqrt(mode + 1.0)
            self._wander[mode] = (
                damping * self._wander[mode]
                + self._random_complex(noise_scale * mode_scale)
            )
        return True

    def _commit_wander(self, constraints: tuple[ValueConstraint, ...]) -> None:
        vanishing_coefficients = _vanishing_coefficients(constraints)
        for mode, wander in enumerate(self._wander):
            for index, coefficient in enumerate(vanishing_coefficients):
                self._anchor_polynomials[mode][index] += wander * coefficient
            self._wander[mode] = 0j

    def _random_complex(self, scale: float) -> complex:
        return complex(
            scale * (2.0 * self._random.random() - 1.0),
            scale * (2.0 * self._random.random() - 1.0),
        )
