import frappe
from frappe import _

custom_fields = {
	"Item": [
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
			"required": 1,
		},
		{
			"fieldname": "item_type",
			"label": _("Item Type"),
			"fieldtype": "Select",
			"insert_after": "itemclscd",
			"options": '\n'.join([i.cdnm for i in frappe.get_doc("RRA Transaction Codes", "Item Type").get("items", [])]),
			"required": 1,
		},
		{
			"fieldname": "tax_type",
			"label": _("Tax Type"),
			"fieldtype": "Select",
			"insert_after": "itemclscd",
			"options": '\n'.join([i.cdnm for i in frappe.get_doc("RRA Transaction Codes", "Taxation Type").get("items", [])]),
			"default": "B-18.00%",
			"required": 1,
		},
		{
			"fieldname": "rra_details_column_1",
			"fieldtype": "Column Break",
			"insert_after": "tax_type",
		},
		{
			"fieldname": "origin_country",
			"label": _("Origin Country"),
			"fieldtype": "Select",
			"insert_after": "rra_details_column_1",
			"options": '\n'.join([i.cdnm for i in frappe.get_doc("RRA Transaction Codes", "Cuntry").get("items", [])]),
			"required": 1,
		},
		{
			"fieldname": "quantity_unit",
			"label": _("Quantity Unit"),
			"fieldtype": "Select",
			"insert_after": "origin_country",
			"options": '\n'.join([i.cdnm for i in frappe.get_doc("RRA Transaction Codes", "Quantity Unit").get("items", [])]),
			"required": 1,
		},
		{
			"fieldname": "rra_pushed",
			"label": _("RRA Pushed"),
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "quantity_unit",
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
