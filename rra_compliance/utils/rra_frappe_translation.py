rra_to_frappe = {
	"Stock I/O Type": "Stock Entry",
	"Payment Type": "Mode of Payment",
	"Taxation Type": "Item Tax Template",
	"Tourism Tax categories": "Sales Taxes and Charges Template",
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
to_replace = {
	'Country': {
		"country_name": "cdNm",
		"code": "cd",
	},
	'UOM': {
		"uom_name": "cdNm",
		"is_packaging_unit": { 'eval': "1 if item.get('cdClsNm') == 'Packing Unit' else 0" },
	},
	"Item Tax Template": {
		"title": "cdNm",
		"taxes": {
			"eval": """
[{
"tax_type": frappe.get_last_doc("Account", filters={"name": ["like", "VAT - %"]}).name,
"tax_rate": 18 if i.get("cd") == "B" else 0
}]
"""
		}
	},
	"Mode of Payment": {
		"mode_of_payment": "cdNm",
		"type": {
			'eval': "'Cash' if 'cash' in i.get('cdNm').lower() else 'Bank' if 'bank' in i.get('cdNm').lower() or 'card' in i.get('cdNm').lower() else 'Phone' if 'mobile' in i.get('cdNm').lower() else 'General'"
		}, # Forgive me father, for I have sinned. May you guide whoever is reading this expression.
		"accounts": {
			"eval": """
[{
"company": frappe.defaults.get_global_default("company"),
"default_account": frappe.get_value("Account", {"account_type": "Cash"}, "name") if 'cash' in i.get('cdNm').lower() or 'mobile' in i.get('cdNm').lower() else frappe.get_value("Account", {"account_type": "Bank"}, "name")
}]
"""
		}
	},
}
