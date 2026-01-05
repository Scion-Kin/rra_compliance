from rra_compliance.setup import RRAComplianceFactory
import frappe

rra = RRAComplianceFactory()
def hourly():
	"""Push Unpushed Data to RRA"""
	items = frappe.get_all("Item", filters={"rra_pushed": 0}, fields=["name"])
	sales_invoices = frappe.get_all("RRA Sales Invoice Log", filters={"rra_pushed": 0}, fields=["sales_invoice"])
	purchase_invoices = frappe.get_all("RRA Purchase Invoice Log", filters={"rra_pushed": 0}, fields=["purchase_invoice"])
	stock_ios = frappe.get_all("RRA Stock IO Log", filters={"rra_pushed": 0}, fields=["stock_ledger_entry"])

	for item in items:
		rra.push_item(item.name)

	for invoice in sales_invoices:
		rra.save_sale(invoice.sales_invoice)

	for invoice in purchase_invoices:
		rra.save_purchase(invoice.purchase_invoice)

	for stock_io in stock_ios:
		rra.update_item_stock(stock_io.stock_ledger_entry)

def weekly():
	"""Fetch RRA Reports"""
	rra.get_item_class(action="update")
	rra.get_codes(action="update")
