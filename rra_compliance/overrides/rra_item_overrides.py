from erpnext.stock.doctype.item.item import Item
from rra_compliance.setup import RRAComplianceFactory


class RRAItemOverrides(Item):
	def __init__(self, *args, **kwargs):
		self.rra = RRAComplianceFactory()

	def after_insert(self):
		super().after_insert()
		self.rra.push_item(str(self.name))

