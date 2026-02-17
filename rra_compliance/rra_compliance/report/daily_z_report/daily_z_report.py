# Copyright (c) 2025, Buffer Punk Ltd and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe


def execute(filters={}):
	columns = [
		{ "fieldname": "sales_invoice", "label": "Sales Invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150 },
		{ "fieldname": "mrc_no", "label": "MRC Number", "fieldtype": "Data", "width": 150 },
		{ "fieldname": "salesDt", "label": "Sale Date", "fieldtype": "Date", "width": 150 },
		{ "fieldname": "salesTyCd", "label": "Sale Type", "fieldtype": "Data", "width": 150 },
		{ "fieldname": "totAmt", "label": "Total Amount", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxblAmtA", "label": "Taxable Amount A", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxblAmtB", "label": "Taxable Amount B", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxblAmtC", "label": "Taxable Amount C", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxblAmtD", "label": "Taxable Amount D", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxAmtA", "label": "Tax Amount A", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxAmtB", "label": "Tax Amount B", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxAmtC", "label": "Tax Amount C", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "taxAmtD", "label": "Tax Amount D", "fieldtype": "Currency", "width": 150 },
		{ "fieldname": "sales_order", "label": "Sales Order", "fieldtype": "Link", "options": "Sales Order", "width": 150 },
		{ "fieldname": "item_count", "label": "Item Count", "fieldtype": "Int", "width": 150 },
	]

	sales_invoices = frappe.db.get_all("Sales Invoice", filters={"posting_date": ["Between", [filters.get("start_date"), filters.get("end_date")]]}, pluck="name")
	logs = frappe.db.get_all("RRA Sales Invoice Log", filters={"sales_invoice": ["in", sales_invoices]}, fields=["*"])
	sales_orders = { i.get("parent"): i.get("sales_order") for i in frappe.db.get_all("Sales Invoice Item", filters={"parent": ["in", sales_invoices]}, fields=["sales_order", "parent"], group_by="parent") }

	for log in logs:
		log.update(**log.get("payload", {}))
		log["item_count"] = len(log.get("itemList", []))
		log["salesDt"] = datetime.strptime(log.get("salesDt"), "%Y%m%d").date()
		log["salesTyCd"] = frappe.get_value("RRA Transaction Codes Item", { "parent" : "Transaction Type", "cd": log.get("salesTyCd") }, 'cdnm')
		log["sales_order"] = sales_orders.get(log.get("sales_invoice"))

	return columns, logs

