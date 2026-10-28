"""Unit tests for server-side money input validation."""
import unittest
from decimal import Decimal

from app import parse_money


class ParseMoneyTests(unittest.TestCase):
    def test_accepts_whole_amount(self):
        self.assertEqual(parse_money("250"), Decimal("250.00"))

    def test_accepts_two_decimal_places(self):
        self.assertEqual(parse_money("250.50"), Decimal("250.50"))

    def test_rejects_zero_and_negative(self):
        for value in ("0", "-1", "-0.50"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_money(value)

    def test_rejects_more_than_two_decimal_places(self):
        with self.assertRaises(ValueError):
            parse_money("12.345")

    def test_rejects_non_numeric_value(self):
        with self.assertRaises(ValueError):
            parse_money("lots")

    def test_rejects_amount_above_demo_limit(self):
        with self.assertRaises(ValueError):
            parse_money("100000000000000000000000000")


if __name__ == "__main__":
    unittest.main()
