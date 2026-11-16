"""Unit-level checks for measured refining output and byproduct limits."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from metal_refinery_tz.metal_refinery_tz.services.refining_rounds import (
    confirmed_finished_fine,
    require_final_outputs,
)


def row(**kwargs):
    return SimpleNamespace(**kwargs)


class TestRefiningRounds(TestCase):
    def test_final_assay_replaces_provisional_output_purity(self):
        batch = row(outputs=[
            row(output_type="Finished Metal", output_lot="LOT-1",
                metal_type="Gold", weight=100, fine_weight=90)
        ])
        assay = row(results=[row(metal_type="Gold", purity_percent=99.5)])
        with patch("metal_refinery_tz.metal_refinery_tz.services.refining_rounds.latest_assay",
                   return_value=assay):
            measured = confirmed_finished_fine(batch)
        self.assertEqual(str(measured["Gold"]), "99.500000")

    def test_missing_final_assay_blocks_confirmation(self):
        batch = row(outputs=[
            row(output_type="Finished Metal", output_lot="LOT-1",
                metal_type="Gold", weight=100)
        ])
        with (
            patch("metal_refinery_tz.metal_refinery_tz.services.refining_rounds.latest_assay",
                  return_value=None),
            patch("frappe.throw", side_effect=ValueError("missing final assay")),
        ):
            with self.assertRaisesRegex(ValueError, "missing final assay"):
                confirmed_finished_fine(batch)

    def test_palladium_cannot_exceed_assayed_content(self):
        batch = row(
            inputs=[row(metal_type="Gold", fine_weight=80, input_weight=100,
                        input_assay="MASY-1")],
            outputs=[row(output_type="Finished Metal", output_lot="PD-1",
                         metal_type="Palladium", weight=10, fine_weight=8)],
        )
        palladium_assay = row(results=[row(metal_type="Palladium", purity_percent=95)])
        feed_assay = row(results=[
            row(metal_type="Gold", purity_percent=80),
            row(metal_type="Palladium", purity_percent=5),
        ])
        with (
            patch("metal_refinery_tz.metal_refinery_tz.services.refining_rounds.latest_assay",
                  return_value=palladium_assay),
            patch("frappe.get_doc", return_value=feed_assay),
            patch("frappe.throw", side_effect=ValueError("excess metal")),
        ):
            with self.assertRaisesRegex(ValueError, "excess metal"):
                require_final_outputs(batch)
