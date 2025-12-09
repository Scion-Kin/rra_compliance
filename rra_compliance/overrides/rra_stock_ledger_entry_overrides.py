from erpnext.stock.doctype.stock_ledger_entry.stock_ledger_entry import StockLedgerEntry
from rra_compliance.setup import RRAComplianceFactory

rra = RRAComplianceFactory()
class RRAStockLedgerEntryOverrides(StockLedgerEntry):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def on_submit(self):
		super().on_submit()
		rra.update_item_stock(self.name)
		rra.update_stock_master(self.name)

