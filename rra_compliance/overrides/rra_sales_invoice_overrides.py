from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

from rra_compliance.setup import RRAComplianceFactory

rra = RRAComplianceFactory()
class RRASalesInvoiceOverrides(SalesInvoice):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def on_submit(self):
		super().on_submit()
		rra.nock_lock(func=rra.save_sale, sales_invoice_id=str(self.name))

