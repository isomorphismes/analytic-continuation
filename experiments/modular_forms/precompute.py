#!/usr/bin/env python3
"""Exact level-1 modular-form q-series precomputation.

The mobile app does not need a CAS at runtime. This script computes the
integer coefficients once and can emit JSON for ARM/GPU experiments.
"""

from __future__ import annotations

import argparse
import json
from typing import Iterable


def divisor_power_sum(n: int, power: int) -> int:
    return sum(d**power for d in range(1, n + 1) if n % d == 0)


def multiply(left: list[int], right: list[int], degree: int) -> list[int]:
    out = [0] * (degree + 1)
    for i, a in enumerate(left):
        if i > degree:
            break
        for j, b in enumerate(right):
            if i + j > degree:
                break
            out[i + j] += a * b
    return out


def power(series: list[int], exponent: int, degree: int) -> list[int]:
    out = [1] + [0] * degree
    base = series[: degree + 1]
    while exponent:
        if exponent & 1:
            out = multiply(out, base, degree)
        exponent >>= 1
        if exponent:
            base = multiply(base, base, degree)
    return out


def divide_unit_series(numerator: list[int], denominator: list[int], degree: int) -> list[int]:
    """Return numerator / denominator through q^degree when denominator[0] == 1."""
    if not denominator or denominator[0] != 1:
        raise ValueError("denominator must have constant coefficient 1")
    out = [0] * (degree + 1)
    for n in range(degree + 1):
        value = numerator[n] if n < len(numerator) else 0
        value -= sum(denominator[k] * out[n - k] for k in range(1, n + 1))
        out[n] = value
    return out


def modular_coefficients(degree: int) -> dict[str, list[int]]:
    work_degree = degree + 1
    e4 = [1] + [240 * divisor_power_sum(n, 3) for n in range(1, work_degree + 1)]
    e6 = [1] + [-504 * divisor_power_sum(n, 5) for n in range(1, work_degree + 1)]

    e4_cubed = power(e4, 3, work_degree)
    e6_squared = power(e6, 2, work_degree)
    delta = []
    for a, b in zip(e4_cubed, e6_squared):
        difference = a - b
        if difference % 1728 != 0:
            raise ArithmeticError("E4^3 - E6^2 lost exact divisibility by 1728")
        delta.append(difference // 1728)

    if delta[0] != 0 or delta[1] != 1:
        raise ArithmeticError("Delta must start q + O(q^2)")

    # q*j = E4^3 / (Delta/q), so this is ordinary unit-series division.
    delta_over_q = delta[1 : degree + 2]
    q_times_j = divide_unit_series(e4_cubed[: degree + 1], delta_over_q, degree)

    return {
        "e4": e4[: degree + 1],
        "e6": e6[: degree + 1],
        "delta": delta[: degree + 1],
        # Entry 0 is the coefficient of q^-1, entry 1 of q^0, etc.
        "j": q_times_j,
    }


def log_q_derivative(coefficients: Iterable[int], first_exponent: int, order: int) -> list[int]:
    """Coefficients of (q d/dq)^order without changing exponent indexing."""
    return [coefficient * (first_exponent + index) ** order for index, coefficient in enumerate(coefficients)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--degree", type=int, default=12)
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()
    if args.degree < 1:
        parser.error("--degree must be at least 1")

    data = modular_coefficients(args.degree)
    data["j_log_q_derivative"] = log_q_derivative(data["j"], -1, 1)

    # Fixtures shared with Sage, ARM and GPU branches.
    assert data["e4"][:5] == [1, 240, 2160, 6720, 17520]
    assert data["e6"][:5] == [1, -504, -16632, -122976, -532728]
    assert data["delta"][:7] == [0, 1, -24, 252, -1472, 4830, -6048]
    assert data["j"][:6] == [1, 744, 196884, 21493760, 864299970, 20245856256]

    print(json.dumps(data, indent=args.indent, sort_keys=True))


if __name__ == "__main__":
    main()
