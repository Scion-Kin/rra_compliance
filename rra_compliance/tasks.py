from rra_compliance.setup import RRAComplianceFactory
import frappe


def hourly():
	"""Push Unpushed Data to RRA"""
	rra = RRAComplianceFactory()
	items = frappe.get_all("Item", filters={"rra_pushed": 0}, fields=["name"])
	sales_invoices = frappe.get_all("RRA Sales Invoice Log", filters={"rra_pushed": 0}, fields=["sales_invoice"])
	purchase_invoices = frappe.get_all("RRA Purchase Invoice Log", filters={"rra_pushed": 0}, fields=["purchase_invoice"])
	for item in items:
		rra.push_item(item.name)
	for invoice in sales_invoices:
		rra.save_sale(invoice.sales_invoice)
	for invoice in purchase_invoices:
		rra.save_purchase(invoice.purchase_invoice)
