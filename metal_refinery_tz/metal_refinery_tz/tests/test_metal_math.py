"""Arithmetic contract: run with a Frappe bench test environment."""
from decimal import Decimal
import unittest

from metal_refinery_tz.metal_refinery_tz.services.metal_math import decimal, weight, fine


class TestMetalMath(unittest.TestCase):
    def test_recovery_weight(self):
        self.assertEqual(fine("125.000000", "99.5"), Decimal("124.375000"))

    def test_zero_purity(self):
        self.assertEqual(fine("10", "0"), Decimal("0.000000"))

    def test_decimal_weight_rounding(self):
        self.assertEqual(weight("1.12345678"), Decimal("1.123457"))

    def test_decimal_converter(self):
        self.assertEqual(decimal("0.000001"), Decimal("0.000001"))
