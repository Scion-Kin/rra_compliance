import frappe
from frappe import _

def create_dependent_custom_fields():
	dependent_custom_fields = get_custom_fields()
	for doctype, fields in dependent_custom_fields.items():
		for field in fields:
			frappe.get_doc({
				"doctype": "DocField",
				"dt": doctype,
				**field,
				"parenttype": "DocType",
				"parent": doctype
			}).insert(ignore_if_duplicate=True)

def create_independent_custom_fields():
	independent_custom_fields = get_independent_custom_fields()
	for doctype, fields in independent_custom_fields.items():
		for field in fields:
			frappe.get_doc({
				"doctype": "DocField",
				"dt": doctype,
				**field,
				"parenttype": "DocType",
				"parent": doctype
			}).insert(ignore_if_duplicate=True)


def delete_all_fields():
	custom_fields = get_custom_fields()
	independent_custom_fields = get_independent_custom_fields()

	for doctype, fields in {**custom_fields, **independent_custom_fields}.items():
		for field in fields:
			try:
				frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]})
			except frappe.DoesNotExistError:
				pass


def get_independent_custom_fields():
	return {
		"UOM": [
			{
				"fieldname": "is_packaging_unit",
				"label": _("Is Packaging Unit"),
				"fieldtype": "Check",
				"insert_after": "stock_uom",
				"read_only": 1
			}
		]
	}

def get_custom_fields():
	return {
		"Item": [
			{
				"fieldname": "package_unit",
				"label": _("Packaging Unit"),
				"fieldtype": "Link",
				"insert_after": "stock_uom",
				"options": 'UOM',
				"default": "Net",
				"reqd": 1,
				"set_only_once": 1,
			},
			{
				"fieldname": "origin_country",
				"label": _("Origin Country"),
				"fieldtype": "Link",
				"insert_after": "package_unit",
				"options": 'Country',
				"default": "RWANDA",
				"reqd": 1,
				"set_only_once": 1,
			},
			{
				"fieldname": "item_type",
				"label": _("Item Type"),
				"fieldtype": "Select",
				"insert_after": "origin_country",
				"options": '\n'.join([i.cdnm.strip() for i in frappe.get_doc("RRA Transaction Codes", "Item Type").get("items", [])]),
				"sortable": 1,
				"reqd": 1,
				"set_only_once": 1,
			},
			{
				"fieldname": "rra_details",
				"label": _("RRA Details"),
				"collapsible": 1,
				"fieldtype": "Section Break",
				"insert_after": "taxes",
			},
			{
				"fieldname": "itemclscd",
				"label": _("Item Class Code"),
				"fieldtype": "Data",
				"insert_after": "rra_details",
				"read_only": 1,
				"fetch_from": "item_group.itemclscd",
				"reqd": 1,
			},
			{
				"fieldname": "tax_type",
				"label": _("Tax Type"),
				"fieldtype": "Select",
				"insert_after": "itemclscd",
				"options": '\n'.join([i.cdnm.strip() for i in frappe.get_doc("RRA Transaction Codes", "Taxation Type").get("items", [])]),
				"default": "B-18.00%",
				"sortable": 1,
				"reqd": 1,
				"set_only_once": 1,
			},
			{
				"fieldname": "rra_pushed",
				"label": _("RRA Pushed"),
				"fieldtype": "Check",
				"read_only": 1,
				"insert_after": "tax_type",
			},
		],
		"Item Group": [
			{
				"fieldname": "rra_details_column_1",
				"fieldtype": "Column Break",
				"insert_after": "useyn",
			},
			{
				"fieldname": "itemclscd",
				"label": _("Item Class Code"),
				"fieldtype": "Data",
				"read_only": 1,
				"insert_after": "rra_details",
			},
			{
				"fieldname": "itemclslvl",
				"label": _("Item Class Level"),
				"fieldtype": "Int",
				"read_only": 1,
				"insert_after": "rra_details_column_1",
			},
			{
				"fieldname": "mjrtgyn",
				"label": _("Is Major Group"),
				"fieldtype": "Check",
				"read_only": 1,
				"insert_after": "itemclslvl",
			},
			{
				"fieldname": "rra_details",
				"label": _("RRA Details"),
				"collapsible": 1,
				"fieldtype": "Section Break",
				"insert_after": "column_break_5",
			},
			{
				"fieldname": "taxtycd",
				"label": _("Taxation Type Code"),
				"fieldtype": "Data",
				"read_only": 1,
				"insert_after": "itemclscd",
			},
			{
				"fieldname": "useyn",
				"label": _("Is Active"),
				"read_only": 1,
				"fieldtype": "Check",
				"insert_after": "taxtycd",
			}
		],
		"Branch": [
			{
				"fieldname": "rra_details",
				"label": _("RRA Details"),
				"collapsible": 1,
				"fieldtype": "Tab Break",
				"insert_after": "branch",
			},
			{
				"fieldname": "bhfid",
				"label": _("Branch ID"),
				"fieldtype": "Data",
				"insert_after": "rra_details",
			},
			{
				"fieldname": "bhfnm",
				"label": _("Branch Name"),
				"fieldtype": "Data",
				"insert_after": "bhfid",
			},
			{
				"fieldname": "bhfsttscd",
				"label": _("Branch Status Code"),
				"fieldtype": "Data",
				"insert_after": "bhfnm",
			},
			{
				"fieldname": "prvncnm",
				"label": _("Province Name"),
				"fieldtype": "Data",
				"insert_after": "bhfsttscd",
			},
			{
				"fieldname": "dstrtnm",
				"label": _("District Name"),
				"fieldtype": "Data",
				"insert_after": "prvncnm",
			},
			{
				"fieldname": "sctrnm",
				"label": _("Sector Name"),
				"fieldtype": "Data",
				"insert_after": "dstrtnm",
			},
			{
				"fieldname": "rra_details_column_1",
				"fieldtype": "Column Break",
				"insert_after": "sctrnm",
			},
			{
				"fieldname": "locdesc",
				"label": _("Location Description"),
				"fieldtype": "Data",
				"insert_after": "rra_details_column_1",
			},
			{
				"fieldname": "mgrnm",
				"label": _("Manager's Name"),
				"fieldtype": "Data",
				"insert_after": "locdesc",
			},
			{
				"fieldname": "mgrtelno",
				"label": _("Manager's Phone Number"),
				"fieldtype": "Data",
				"insert_after": "mgrnm",
			},
			{
				"fieldname": "mgremail",
				"label": _("Manager's Email"),
				"fieldtype": "Data",
				"insert_after": "mgrtelno",
			},
			{
				"fieldname": "hqyn",
				"label": _("Is Headquarters"),
				"fieldtype": "Check",
				"insert_after": "mgremail",
			}
		],
		"Customer": [
			{
				"fieldname": "taxprsttscd",
				"label": _("Taxpayer Status Code"),
				"fieldtype": "Data",
				"insert_after": "tax_category",
			}
		]
	}

if __name__ == "__main__":
	pass
	# This is just to avoid linting errors
