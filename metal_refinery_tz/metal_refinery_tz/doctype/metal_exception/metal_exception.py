import frappe
from frappe import _
from frappe.model.document import Document


class MetalException(Document):
    def validate(self):
        if self.approved_by and not self.approval_date:
            frappe.throw(_("Approval date is required with approver"))

    def before_submit(self):
        if not self.approved_by or not self.approval_date:
            frappe.throw(_("Exception approval identity and date are required"))
        if self.approved_by == self.owner:
            frappe.throw(_("The exception creator cannot approve their own exception"))
        if self.approved_by != frappe.session.user:
            frappe.throw(_("Only the named approver may submit this exception"))
