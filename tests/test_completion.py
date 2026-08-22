import unittest

from analytic_continuation.completion import (
    UnderdeterminedPolynomialFamily,
    ValueConstraint,
    compose_coefficients,
    evaluate_coefficients,
)


class CompletionTests(unittest.TestCase):
    def test_constraints_are_exact(self) -> None:
        constraints = [
            ValueConstraint(-1 + 0j, 0 + 0j),
            ValueConstraint(0 + 0j, 1 + 0j),
            ValueConstraint(1 + 0j, 0 + 1j),
        ]
        coefficients = compose_coefficients(
            5,
            constraints,
            [0.2 + 0.1j, -0.05 + 0.08j, 0.03 - 0.02j],
        )
        for constraint in constraints:
            self.assertAlmostEqual(
                abs(
                    evaluate_coefficients(coefficients, constraint.domain)
                    - constraint.value
                ),
                0.0,
                places=10,
            )

    def test_exact_new_value_keeps_older_values_fixed(self) -> None:
        family = UnderdeterminedPolynomialFamily(maximum_degree=4, random_seed=5)
        first = family.constrain_value(-0.5 + 0.2j, 0.0 + 0.0j)
        second = family.constrain_value(0.6 - 0.1j, 1.0 + 0.0j)

        for _ in range(80):
            family.step()

        self.assertAlmostEqual(abs(family.evaluate(first.domain)), 0.0, places=9)
        self.assertAlmostEqual(
            abs(family.evaluate(second.domain) - 1.0),
            0.0,
            places=9,
        )

    def test_locking_a_point_does_not_jump_the_current_function(self) -> None:
        family = UnderdeterminedPolynomialFamily(random_seed=4)
        before = family.coefficients
        family.lock_current_value(0.4 - 0.3j)
        after = family.coefficients

        for left, right in zip(before, after):
            self.assertAlmostEqual(abs(left - right), 0.0, places=10)
        self.assertEqual(family.remaining_complex_dimensions, 7)

    def test_locked_value_survives_random_wandering(self) -> None:
        family = UnderdeterminedPolynomialFamily(random_seed=12)
        constraint = family.lock_current_value(-0.7 + 0.25j)

        for _ in range(120):
            self.assertTrue(family.step())

        self.assertAlmostEqual(
            abs(family.evaluate(constraint.domain) - constraint.value),
            0.0,
            places=9,
        )

    def test_each_new_point_removes_one_complex_dimension(self) -> None:
        family = UnderdeterminedPolynomialFamily(maximum_degree=3, random_seed=1)
        domains = [-1.0 + 0j, -0.3 + 0.4j, 0.5 - 0.2j, 1.0 + 0.5j]

        self.assertEqual(family.remaining_complex_dimensions, 4)
        for expected_remaining, domain in zip((3, 2, 1, 0), domains):
            family.lock_current_value(domain)
            self.assertEqual(
                family.remaining_complex_dimensions,
                expected_remaining,
            )

    def test_fully_determined_family_stops_moving(self) -> None:
        family = UnderdeterminedPolynomialFamily(maximum_degree=2, random_seed=9)
        for domain in (-1.0 + 0j, 0.0 + 0j, 1.0 + 0j):
            family.lock_current_value(domain)

        frozen = family.coefficients
        self.assertFalse(family.step())
        self.assertEqual(family.coefficients, frozen)

    def test_duplicate_constraint_point_is_rejected(self) -> None:
        family = UnderdeterminedPolynomialFamily(random_seed=2)
        family.lock_current_value(0.25 + 0.75j)

        with self.assertRaisesRegex(ValueError, "already constrained"):
            family.lock_current_value(0.25 + 0.75j)


if __name__ == "__main__":
    unittest.main()
