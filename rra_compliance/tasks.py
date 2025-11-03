import frappe
from rra_compliance.setup import RRAComplianceFactory


def hourly():
	"""Push Unpushed Data to RRA"""
	rra = RRAComplianceFactory()
	items = frappe.get_all("Item", filters={"rra_pushed": 0}, fields=["name"])
	invoices = frappe.get_all("RRA Sales Invoice Log", filters={"rra_pushed": 0}, fields=["sales_invoice"])
	for item in items:
		rra.push_item(item.name)
	for invoice in invoices:
		rra.save_sale(invoice.sales_invoice)
