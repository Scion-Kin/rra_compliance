# Copyright (c) 2025, Buffer Punk and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RRAPurchaseInvoiceLog(Document):
	def autoname(self):
		self.name = f"RRA-PIL-{self.invc_no}"
