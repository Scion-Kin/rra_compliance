from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from rra_compliance.setup import RRAComplianceFactory
import frappe

rra = RRAComplianceFactory()
class RRAPurchaseInvoiceOverrides(PurchaseInvoice):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def on_submit(self):
		super().on_submit()
		pushed = frappe.get_value("RRA Purchase Invoice Log", {"purchase_invoice": self.name, "docstatus": 1}, "rra_pushed")
		if not pushed:
			rra.save_purchase(str(self.name))
