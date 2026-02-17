# Copyright (c) 2025, Buffer Punk Ltd and contributors
# For license information, please see license.txt

import frappe


def execute(filters={}):
	columns = [
		{ "fieldname": "sales_invoice", "label": "Sales Invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150 },
		{ "fieldname": "itemCd", "label": "Item Code", "fieldtype": "Data", "width": 150 },
		{ "fieldname": "itemNm", "label": "Item Name", "fieldtype": "Data", "width": 200 },
		{ "fieldname": "prc", "label": "Unit Price", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "totAmt", "label": "Total Amount", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxAmt", "label": "Tax Amount", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "qty", "label": "Quantity Sold", "fieldtype": "Float", "width": 150 },
		{ "fieldname": "stock_qty", "label": "Remaining Stock Quantity", "fieldtype": "Float", "width": 150 },
	]

	sales_invoices = frappe.db.get_all("Sales Invoice", filters={"docstatus": 1, "posting_date": ["Between", [filters.get("start_date"), filters.get("end_date")]]}, pluck="name")
	logs = frappe.db.get_all("RRA Sales Invoice Log", filters={"docstatus": 1, "sales_invoice": ["in", sales_invoices]}, fields=["*"])

	items = []
	for log in logs:
		log_items = frappe.parse_json(log.get("payload", {})).get("itemList", [])
		for item in log_items:
			legder_qty = frappe.db.get_value("Stock Ledger Entry", {"voucher_no": log.sales_invoice, "item_code": item.get("itemCd")}, "qty_after_transaction")
			items.append(item.update({"sales_invoice": log.sales_invoice, "stock_qty": legder_qty}))

	return columns, items

