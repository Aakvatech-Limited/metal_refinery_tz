"""Contract tests for draft-only ERPNext posting bridge.

Run inside a Frappe/ERPNext test bench; this file does not submit or post ledgers.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe import ValidationError

from metal_refinery_tz.metal_refinery_tz.services.posting_bridge import (
    create_purchase_receipt_draft,
    create_toll_sales_invoice_draft,
    create_operating_cost_invoices,
    create_wip_transfer_draft,
    validate_operating_costs,
    validate_profile,
)


class TestDraftPostingBridge(unittest.TestCase):
    def test_disabled_profile_creates_no_receipt(self):
        with patch(
            "metal_refinery_tz.metal_refinery_tz.services.posting_bridge.get_enabled_profile",
            return_value=None,
        ):
            create_purchase_receipt_draft(SimpleNamespace(company="TEST", purchase_receipt=None))

    def test_disabled_profile_creates_no_sales_invoice(self):
        with patch(
            "metal_refinery_tz.metal_refinery_tz.services.posting_bridge.get_enabled_profile",
            return_value=None,
        ):
            create_toll_sales_invoice_draft(SimpleNamespace(company="TEST", sales_invoice=None))

    def test_disabled_profile_creates_no_cost_invoice(self):
        row = SimpleNamespace(supplier="TEST", purchase_invoice=None)
        doc = SimpleNamespace(company="TEST", operating_costs=[row])
        with patch(
            "metal_refinery_tz.metal_refinery_tz.services.posting_bridge.get_enabled_profile",
            return_value=None,
        ):
            create_operating_cost_invoices(doc)

    def test_disabled_profile_creates_no_stock_entry(self):
        doc = SimpleNamespace(company="TEST", stock_entry=None, ownership="Company Owned")
        with patch(
            "metal_refinery_tz.metal_refinery_tz.services.posting_bridge.get_enabled_profile",
            return_value=None,
        ):
            create_wip_transfer_draft(doc)

    def test_operating_cost_rejects_negative_rate(self):
        row = SimpleNamespace(qty=1, rate=-1, supplier="TEST", item_code="TEST")
        doc = {"operating_costs": [row]}
        with self.assertRaises(ValidationError):
            validate_operating_costs(SimpleNamespace(
                get=lambda key: doc.get(key), company="TEST"
            ))

    def test_enabled_profile_requires_accounts(self):
        profile = SimpleNamespace(
            company="TEST", cost_center="TEST", project=None,
            receipt_warehouse=None, wip_warehouse=None, finished_warehouse=None,
            expense_account=None, income_account=None, purchase_item=None,
            toll_service_item=None, auto_create_drafts=1,
            get=lambda key: None,
        )
        with patch("metal_refinery_tz.metal_refinery_tz.services.posting_bridge._company_link"):
            with self.assertRaises(ValidationError):
                validate_profile(profile)
