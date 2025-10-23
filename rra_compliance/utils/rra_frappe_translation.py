rra_to_frappe = {
	"Stock I/O Type": "Stock Entry",
	"Payment Type": "Payment Entry",
	"Taxation Type": "Sales Taxes and Charges",
	"Tourism Tax categories": "Sales Taxes and Charges",
	"Quantity Unit": "UOM",
	"Unit Type": "UOM",
	"Sale Status": "Sales Order",
	"Purchase Status": "Purchase Order",
	"Import Item Status": "Item",
	"Packing Unit": "UOM",
	"Business Nature": "Industry Type",
	"Item Type": "Item",
	"Refund Reason": "Sales Invoice",
	"Reason of Inventory Adjustment": "Stock Reconciliation",
	"Bank": "Bank",
	"Sales Receipt Type": "Sales Invoice",
	"Purchase Receipt Type": "Purchase Receipt",
	"Currency": "Currency",
	"LOCALE": "Language",
	"Item Category": "Item",
	"Branch Status": "Company",
	"Cuntry": "Country",
}

frappe_to_rra = {v: k for k, v in rra_to_frappe.items()}

