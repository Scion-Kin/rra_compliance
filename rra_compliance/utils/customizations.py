from frappe import _

custom_fields = {
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
			"insert_after": "rra_details",
		},
		{
			"fieldname": "itemclslvl",
			"label": _("Item Class Level"),
			"fieldtype": "Int",
			"insert_after": "rra_details_column_1",
		},
		{
			"fieldname": "mjrtgyn",
			"label": _("Is Major Group"),
			"fieldtype": "Check",
			"insert_after": "itemclslvl",
		},
		{
			"fieldname": "rra_details",
			"fieldtype": "Section Break",
			"insert_after": "column_break_5",
		},
		{
			"fieldname": "taxtycd",
			"label": _("Taxation Type Code"),
			"fieldtype": "Data",
			"insert_after": "itemclscd",
		},
		{
			"fieldname": "useyn",
			"label": _("Is Active"),
			"fieldtype": "Check",
			"insert_after": "taxtycd",
		}
	],
}
