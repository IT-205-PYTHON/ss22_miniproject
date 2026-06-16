"""
test_energy.py
--------------
Unit tests for the Smart Energy Monitor — focuses on
calculate_energy_financials() covering the three boundary cases
specified in the SRS.

Run with:
    python -m unittest test_energy.py -v
"""

import unittest

from energy_monitor import (
    BASE_RATE_VND_PER_KWH,
    DISCOUNT_RATE,
    DISCOUNT_THRESHOLD_KWH,
    STATUS_NORMAL,
    STATUS_OVERLOAD,
    calculate_energy_financials,
)


def _make_device(
    device_id: str,
    old_index: int,
    new_index: int,
    status: str = STATUS_NORMAL,
) -> dict:
    """
    Helper — build a minimal device dict for test fixtures.

    Args:
        device_id:  Unique device identifier.
        old_index:  Previous meter reading (kWh).
        new_index:  Current meter reading (kWh).
        status:     Operational status string.

    Returns:
        A device dictionary compatible with energy_monitor functions.
    """
    return {
        "id": device_id,
        "location": "Test Location",
        "old_index": old_index,
        "new_index": new_index,
        "status": status,
    }


class TestCalculateEnergyFinancials(unittest.TestCase):
    """
    Test suite for calculate_energy_financials().

    SRS boundary cases:
        Case 1 — Total consumption BELOW discount threshold (< 50,000 kWh)
                 → discount = 0 %
        Case 2 — Total consumption AT the discount threshold (= 50,000 kWh)
                 → discount = 3 %
        Case 3 — Total consumption ABOVE the discount threshold (> 50,000 kWh)
                 → discount = 3 %
    """

    # ------------------------------------------------------------------
    # Case 1: below threshold — no discount
    # ------------------------------------------------------------------
    def test_below_threshold_no_discount(self) -> None:
        """
        Total < 50,000 kWh must yield 0 % discount and full gross cost.
        """
        devices = [
            _make_device("M01", 0, 20_000),
            _make_device("M02", 0, 10_000),
        ]
        total_kwh, discount_pct, total_cost = (
            calculate_energy_financials(devices)
        )

        expected_kwh = 30_000
        expected_discount = 0.0
        expected_cost = expected_kwh * BASE_RATE_VND_PER_KWH

        self.assertEqual(total_kwh, expected_kwh)
        self.assertAlmostEqual(discount_pct, expected_discount)
        self.assertAlmostEqual(total_cost, expected_cost)

    # ------------------------------------------------------------------
    # Case 2: exactly at threshold — discount applies
    # ------------------------------------------------------------------
    def test_at_threshold_discount_applied(self) -> None:
        """
        Total == 50,000 kWh must yield 3 % discount.
        """
        devices = [
            _make_device("M01", 0, 30_000),
            _make_device("M02", 0, 20_000),
        ]
        total_kwh, discount_pct, total_cost = (
            calculate_energy_financials(devices)
        )

        expected_kwh = 50_000
        expected_discount = DISCOUNT_RATE
        gross = expected_kwh * BASE_RATE_VND_PER_KWH
        expected_cost = gross * (1 - DISCOUNT_RATE)

        self.assertEqual(total_kwh, expected_kwh)
        self.assertAlmostEqual(discount_pct, expected_discount)
        self.assertAlmostEqual(total_cost, expected_cost)

    # ------------------------------------------------------------------
    # Case 3: above threshold — discount applies
    # ------------------------------------------------------------------
    def test_above_threshold_discount_applied(self) -> None:
        """
        Total > 50,000 kWh must yield 3 % discount and reduced cost.
        """
        devices = [
            _make_device("M01", 1_200, 4_500),   #  3,300 kWh
            _make_device("M02", 2_300, 8_500),   #  6,200 kWh
            _make_device("M03", 5_000, 60_000),  # 55,000 kWh
        ]
        total_kwh, discount_pct, total_cost = (
            calculate_energy_financials(devices)
        )

        expected_kwh = 3_300 + 6_200 + 55_000   # 64,500 kWh
        expected_discount = DISCOUNT_RATE
        gross = expected_kwh * BASE_RATE_VND_PER_KWH
        expected_cost = gross * (1 - DISCOUNT_RATE)

        self.assertEqual(total_kwh, expected_kwh)
        self.assertAlmostEqual(discount_pct, expected_discount)
        self.assertAlmostEqual(total_cost, expected_cost)

    # ------------------------------------------------------------------
    # Additional: empty device list
    # ------------------------------------------------------------------
    def test_empty_device_list(self) -> None:
        """An empty device list must return zeros with no discount."""
        total_kwh, discount_pct, total_cost = (
            calculate_energy_financials([])
        )
        self.assertEqual(total_kwh, 0)
        self.assertAlmostEqual(discount_pct, 0.0)
        self.assertAlmostEqual(total_cost, 0.0)

    # ------------------------------------------------------------------
    # Additional: return type must be a tuple
    # ------------------------------------------------------------------
    def test_return_type_is_tuple(self) -> None:
        """calculate_energy_financials must return a tuple of 3 elements."""
        result = calculate_energy_financials(
            [_make_device("X01", 0, 10_000)]
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

    # ------------------------------------------------------------------
    # Additional: single device, below threshold
    # ------------------------------------------------------------------
    def test_single_device_below_threshold(self) -> None:
        """Single device consuming 3,300 kWh → no discount."""
        devices = [_make_device("M01", 1_200, 4_500)]
        total_kwh, discount_pct, total_cost = (
            calculate_energy_financials(devices)
        )
        self.assertEqual(total_kwh, 3_300)
        self.assertAlmostEqual(discount_pct, 0.0)
        self.assertAlmostEqual(
            total_cost, 3_300 * BASE_RATE_VND_PER_KWH
        )

    # ------------------------------------------------------------------
    # Additional: Overload device still counted in financials
    # ------------------------------------------------------------------
    def test_overload_device_included_in_total(self) -> None:
        """Devices with Overload status must still contribute to totals."""
        devices = [
            _make_device("M01", 0, 10_000, STATUS_NORMAL),
            _make_device("M02", 0, 45_000, STATUS_OVERLOAD),
        ]
        total_kwh, _, _ = calculate_energy_financials(devices)
        self.assertEqual(total_kwh, 55_000)


class TestDiscountThresholdBoundary(unittest.TestCase):
    """Edge cases exactly one unit either side of the threshold."""

    def test_one_kwh_below_threshold(self) -> None:
        """49,999 kWh must yield 0 % discount."""
        devices = [_make_device("X", 0, 49_999)]
        _, discount_pct, _ = calculate_energy_financials(devices)
        self.assertAlmostEqual(discount_pct, 0.0)

    def test_one_kwh_above_threshold(self) -> None:
        """50,001 kWh must yield 3 % discount."""
        devices = [_make_device("X", 0, 50_001)]
        _, discount_pct, _ = calculate_energy_financials(devices)
        self.assertAlmostEqual(discount_pct, DISCOUNT_RATE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
