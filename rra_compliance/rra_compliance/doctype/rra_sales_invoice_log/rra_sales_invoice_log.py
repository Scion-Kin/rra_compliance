# Copyright (c) 2025, Buffer Punk and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RRASalesInvoiceLog(Document):
	def autoname(self):
		self.name = f"RRA-SIL-{self.invc_no}"
