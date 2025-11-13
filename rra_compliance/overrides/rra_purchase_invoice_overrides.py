from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from rra_compliance.setup import RRAComplianceFactory

rra = RRAComplianceFactory()
class RRAPurchaseInvoiceOverrides(PurchaseInvoice):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def on_submit(self):
		super().on_submit()
		rra.save_purchase(str(self.name))
