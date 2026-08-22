import unittest

from analytic_continuation.completion import UnderdeterminedAnalyticFamily


class CompletionTests(unittest.TestCase):
    def test_family_is_transcendental(self) -> None:
        family = UnderdeterminedAnalyticFamily(random_seed=3)
        self.assertTrue(family.is_transcendental)
        self.assertTrue(any(abs(frequency) > 0 for frequency in family.mode_frequencies))

    def test_exact_new_values_survive_random_wandering(self) -> None:
        family = UnderdeterminedAnalyticFamily(random_seed=5)
        first = family.constrain_value(-0.5 + 0.2j, 0.0 + 0.0j)
        second = family.constrain_value(0.6 - 0.1j, 1.0 + 0.0j)

        for _ in range(120):
            family.step()

        self.assertAlmostEqual(abs(family.evaluate(first.domain)), 0.0, places=9)
        self.assertAlmostEqual(
            abs(family.evaluate(second.domain) - 1.0),
            0.0,
            places=9,
        )

    def test_locking_a_point_preserves_the_whole_current_frame(self) -> None:
        family = UnderdeterminedAnalyticFamily(random_seed=4)
        for _ in range(30):
            family.step()

        probes = (-0.9 + 0.4j, 0.2 - 0.7j, 1.1 + 0.25j)
        before = [family.evaluate(probe) for probe in probes]
        family.lock_current_value(0.4 - 0.3j)
        after = [family.evaluate(probe) for probe in probes]

        for left, right in zip(before, after):
            self.assertAlmostEqual(abs(left - right), 0.0, places=10)

    def test_constraints_damp_but_do_not_exhaust_motion(self) -> None:
        family = UnderdeterminedAnalyticFamily(random_seed=1)
        initial_motion_scale = family.motion_scale
        domains = [
            -1.0 + 0.0j,
            -0.7 + 0.5j,
            -0.3 - 0.6j,
            0.0 + 0.8j,
            0.25 - 0.75j,
            0.5 + 0.4j,
            0.8 - 0.2j,
            1.1 + 0.6j,
        ]
        for domain in domains:
            family.lock_current_value(domain)

        self.assertLess(family.motion_scale, initial_motion_scale)
        self.assertEqual(family.constraint_slots_remaining, 4)

        fixed = [(constraint.domain, family.evaluate(constraint.domain)) for constraint in family.constraints]
        probe = 0.33 + 0.61j
        before = family.evaluate(probe)
        for _ in range(180):
            self.assertTrue(family.step())
        after = family.evaluate(probe)

        self.assertGreater(abs(after - before), 1.0e-7)
        for domain, value in fixed:
            self.assertAlmostEqual(abs(family.evaluate(domain) - value), 0.0, places=8)

    def test_duplicate_constraint_point_is_rejected(self) -> None:
        family = UnderdeterminedAnalyticFamily(random_seed=2)
        family.lock_current_value(0.25 + 0.75j)

        with self.assertRaisesRegex(ValueError, "already constrained"):
            family.lock_current_value(0.25 + 0.75j)


if __name__ == "__main__":
    unittest.main()
