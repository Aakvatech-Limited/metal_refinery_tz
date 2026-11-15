"""Stage 4 contract tests. Requires a Frappe/ERPNext test bench."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import frappe

from metal_refinery_tz.metal_refinery_tz.services.bullion import validate_export
from metal_refinery_tz.metal_refinery_tz.services.tolling import validate_agreement


class TestStage4(unittest.TestCase):
    def test_agreement_rejects_duplicate_metal_rates(self):
        doc = SimpleNamespace(
            valid_from="2026-01-01", valid_to="2026-12-31",
            rates=[
                SimpleNamespace(metal_type="Gold", rate_per_weight_unit=10, minimum_fee=0),
                SimpleNamespace(metal_type="Gold", rate_per_weight_unit=12, minimum_fee=0),
            ],
        )
        with self.assertRaises(frappe.ValidationError):
            validate_agreement(doc)

    def test_agreement_rejects_invalid_dates(self):
        doc = SimpleNamespace(valid_from="2026-12-31", valid_to="2026-01-01", rates=[])
        with self.assertRaises(frappe.ValidationError):
            validate_agreement(doc)

    def test_export_requires_verified_evidence(self):
        release = SimpleNamespace(docstatus=1, company="Refinery", customer="Customer A")
        doc = SimpleNamespace(
            release_authorization="MRLS-001", company="Refinery", customer="Customer A",
            checklist=[SimpleNamespace(
                requirement="Export permit", evidence_reference="", verified=0, verified_by=None
            )],
            sales_invoice=None, delivery_note=None,
        )
        with patch("frappe.get_doc", return_value=release):
            with self.assertRaises(frappe.ValidationError):
                validate_export(doc)
