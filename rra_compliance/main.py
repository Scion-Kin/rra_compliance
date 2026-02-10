from datetime import datetime

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from frappe.utils import getdate

from rra_compliance.setup import RRAComplianceFactory

rra = RRAComplianceFactory()

@frappe.whitelist()
def initialize_company(company, dvcSrlNo=None):
	"""Initialize RRA for a Company"""
	if not dvcSrlNo:
		frappe.throw("Device Serial Number is required")

	rra.set_payload(company)
	rra.initialize(company=company, dvcSrlNo=dvcSrlNo, out="frappe")


@frappe.whitelist()
def get_purchases(company: str, from_date: str):
	"""Fetch Purchases from RRA"""
	rra.set_payload(company)
	return rra.get_purchases(date=getdate(from_date))


@frappe.whitelist()
def get_imported_items(company: str, from_date: str):
	"""Fetch Purchases from RRA"""
	rra.set_payload(company)
	return rra.get_imported_items(date=getdate(from_date))


@frappe.whitelist()
def save_mapped_purchases(company: str, purchases):
	"""Save Mapped Purchases from RRA"""
	try:
		rra.set_payload(company)
		purchases = frappe.parse_json(purchases)
		for purchase in purchases:
			doc = frappe.get_doc({
				"doctype": "Purchase Invoice",
				"company": company,
				"supplier": purchase.get("spplrNm"),
				"is_paid": 1,
				"posting_date": datetime.strptime(purchase.get("cfmDt"), "%Y-%m-%d %H:%M:%S").date(),
				"posting_time": datetime.strptime(purchase.get("cfmDt"), "%Y-%m-%d %H:%M:%S").time(),
				"bill_date": datetime.strptime(purchase.get("cfmDt"), "%Y-%m-%d %H:%M:%S").date(),
				"bill_no": purchase.get("spplrInvcNo"),
				"mode_of_payment": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Payment Type", "cd": purchase.get("pmtTyCd") }, 'cdnm'),
				"paid_amount": purchase.get("totAmt"),
				"sdc_id": purchase.get("sdcId") or purchase.get("spplrSdcId"),
			})
			doc.cash_bank_account = get_bank_cash_account(doc.mode_of_payment, company).get('account')
			for item in purchase.get("itemList", []):
				doc.append("items", {
					"item_name": item.get("itemNm"),
					"item_code": item.get("itemCd"),
					"qty": item.get("qty"),
					"rate": item.get("prc"),
					"basic_rate": item.get("prc")
				})
			doc.insert()
			doc.submit()
			frappe.db.commit()
		return "Purchases saved successfully"

	except Exception as e:
		frappe.throw(f"Error saving purchases: {e}")


@frappe.whitelist()
def update_imported_items(company: str, itemList):
	""" Wrapper to update imported items from RRA """
	try:
		rra.set_payload(company)
		items = frappe.parse_json(itemList)
		if next((item for item in items if not item.get("imptItemsttsCd")), None):
			frappe.throw("All items must have an Import Item Status Code")

		rra.update_imported_items(items)
		return "Items updated successfully"

	except Exception as e:
		frappe.throw(f"Error updating items: {e}")
