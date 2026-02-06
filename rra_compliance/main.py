import frappe
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
def save_mapped_purchases(company, purchases):
	"""Save Mapped Purchases from RRA"""
	for purchase in purchases:
		doc = frappe.get_doc({
			"doctype": "Purchase Invoice",
			"company": company,
			"supplier": purchase.get("spplrNm"),
			"is_paid": 1,
			"posting_date": purchase.get("salesDt"),
			"bill_date": purchase.get("salesDt"),
			"bill_no": purchase.get("spplrInvcNo"),
			"sdc_id": purchase.get("sdcId") or purchase.get("spplrSdcId"),
			"items": purchase.get("items"),
		})
		doc.insert(ignore_permissions=True)

