#!/usr/bin/env sage -python
"""Exact q-expansion reference for the level-1 modular experiment."""

from __future__ import annotations

import argparse

from sage.all import QQ
from sage.modular.modform.eis_series import eisenstein_series_qexp
from sage.modular.modform.j_invariant import j_invariant_qexp
from sage.modular.modform.vm_basis import delta_qexp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--precision", type=int, default=16)
    parser.add_argument("--derivative-order", type=int, default=1)
    args = parser.parse_args()
    if args.precision < 5:
        parser.error("--precision must be at least 5")
    if args.derivative_order < 0:
        parser.error("--derivative-order must be nonnegative")

    precision = args.precision
    e4 = eisenstein_series_qexp(4, precision, K=QQ, normalization="constant")
    e6 = eisenstein_series_qexp(6, precision, K=QQ, normalization="constant")
    delta = delta_qexp(precision, K=QQ)
    j = j_invariant_qexp(precision - 1, K=QQ)

    # Exact ring identity, truncated to the requested q-adic precision.
    assert (e4**3 - e6**2).add_bigoh(precision) == (1728 * delta).add_bigoh(precision)

    # These first terms are the common fixture used by the other branches.
    assert j[-1] == 1
    assert j[0] == 744
    assert j[1] == 196884
    assert j[2] == 21493760

    order = args.derivative_order
    derivative_coefficients = {
        exponent: (exponent**order) * j[exponent]
        for exponent in range(-1, precision - 1)
    }

    print("E4 =", e4)
    print("E6 =", e6)
    print("Delta =", delta)
    print("j =", j)
    print(f"(q d/dq)^{order} j coefficients =", derivative_coefficients)
    print("d/dtau = 2*pi*i * q*d/dq, so q-expansion coefficients give tau derivatives directly")


if __name__ == "__main__":
    main()
