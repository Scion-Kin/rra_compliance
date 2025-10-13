from erpnext.stock.doctype.item.item import Item
from rra_compliance.setup import RRAComplianceFactory


class RRAItemOverrides(Item):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.rra = RRAComplianceFactory()

	def on_update(self):
		super().on_update()
		if not self.get('rra_pushed'):
			self.rra.push_item(str(self.name))

