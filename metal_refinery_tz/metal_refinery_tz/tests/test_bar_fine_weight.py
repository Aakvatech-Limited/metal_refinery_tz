"""Regression tests for batch fine-metal conservation during bar registration.

Run with: bench --site SITE run-tests --app metal_refinery_tz
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from metal_refinery_tz.metal_refinery_tz.services.bullion import validate_bar


def _bar(fine_gross, name=None):
    return SimpleNamespace(
        name=name,
        refining_batch="RBAT-TEST-001",
        company="Test Company",
        metal_type="Gold",
        ownership="Company Owned",
        owner_customer=None,
        uom="Gram",
        weight=fine_gross,
        purity_percent=100,
        fine_weight=None,
        warehouse=None,
        status="In Vault",
        get_doc_before_save=lambda: None,
    )


def _batch(input_fine=100, finished_fine=100):
    return SimpleNamespace(
        name="RBAT-TEST-001",
        docstatus=1,
        company="Test Company",
        metal_type="Gold",
        ownership="Company Owned",
        weight_uom="Gram",
        inputs=[SimpleNamespace(fine_weight=input_fine)],
        outputs=[SimpleNamespace(output_type="Finished Metal", fine_weight=finished_fine)],
    )


class TestBarFineWeight(unittest.TestCase):
    def _validate(self, bar, batch, existing=None):
        with (
            patch("frappe.qb"),
            patch("frappe.get_doc", return_value=batch),
            patch("frappe.get_all", return_value=existing or []),
        ):
            validate_bar(bar)

    def test_exact_available_quantity_is_allowed(self):
        bar = _bar(40)
        self._validate(bar, _batch(100, 95), [SimpleNamespace(name="OLD", fine_weight=55)])
        self.assertEqual(bar.fine_weight, 40)

    def test_multiple_bars_cannot_exceed_finished_output(self):
        with self.assertRaises(frappe.ValidationError):
            self._validate(
                _bar(46), _batch(100, 95), [SimpleNamespace(name="OLD", fine_weight=50)]
            )

    def test_incorrect_finished_output_cannot_exceed_input_purity(self):
        with self.assertRaises(frappe.ValidationError):
            self._validate(_bar(101), _batch(100, 110))

    def test_no_finished_metal_cannot_be_registered(self):
        with self.assertRaises(frappe.ValidationError):
            self._validate(_bar(1), _batch(100, 0))

    def test_existing_record_is_excluded_when_revalidating(self):
        bar = _bar(40, name="SAME")
        self._validate(
            bar, _batch(100, 100),
            [SimpleNamespace(name="SAME", fine_weight=40), SimpleNamespace(name="OTHER", fine_weight=60)],
        )

    def test_no_one_microgram_overage_is_permitted(self):
        with self.assertRaises(frappe.ValidationError):
            self._validate(_bar(0.000002), _batch(1, 1), [
                SimpleNamespace(name="OLD", fine_weight=0.999999)
            ])
