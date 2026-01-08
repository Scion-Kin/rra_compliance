import frappe
from rra_compliance.setup import RRAComplianceFactory

rra = RRAComplianceFactory()


@frappe.whitelist()
def initialize_company(company, dvcSrlNo=None):
	"""Initialize RRA for a Company"""
	if not dvcSrlNo:
		frappe.throw("Device Serial Number is required")

	rra.set_payload(company)
	rra.initialize(company=company, dvcSrlNo=dvcSrlNo, out="frappe")
