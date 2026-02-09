from erpnext.stock.doctype.item.item import Item
from rra_compliance.setup import RRAComplianceFactory
from frappe.exceptions import DoesNotExistError
import frappe

rra = RRAComplianceFactory()
class RRAItemOverrides(Item):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def autoname(self):
		if self.get('item_code'):
			self.name = self.get('item_code')
			return

		country = frappe.get_value("RRA Transaction Codes Item", { "parent" : "Cuntry", "cdnm": self.get('origin_country') }, 'cd')
		item_type = frappe.get_value("RRA Transaction Codes Item", { "parent" : "Item Type", "cdnm": self.get('item_type') }, 'cd')
		package_unit = frappe.get_value("RRA Transaction Codes Item", { "parent" : "Packing Unit", "cdnm": self.get('package_unit').split(' - ')[0] }, 'cd')
		quantity_unit = frappe.get_value("RRA Transaction Codes Item", { "parent" : "Quantity Unit", "cdnm": self.get('stock_uom').split(' - ')[0] }, 'cd')

		prefix = f"{country}{item_type}{package_unit}{quantity_unit}"

		try:
			last_doc = frappe.get_last_doc("Item", {"name": ["like", f"{prefix}%"]}).name
		except DoesNotExistError:
			last_doc = f"{prefix}000000"

		last_sequence = int(last_doc.replace(prefix, "")) + 1
		self.name = f"{prefix}{str(last_sequence).zfill(6)}"
		self.item_code = self.name

	def after_insert(self):
		super().after_insert()
		if not self.get('rra_pushed'):
			rra.push_item(str(self.name))
