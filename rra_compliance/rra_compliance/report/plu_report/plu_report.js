// Copyright (c) 2025, Buffer Punk Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["PLU Report"] = {
	"filters": [
		{
			"fieldname": "start_date",
			"fieldtype": "Date",
			"label": "Start Date",
			"mandatory": 1,
			"wildcard_filter": 0
		},
		{
			"fieldname": "end_date",
			"fieldtype": "Date",
			"label": "End Date",
			"mandatory": 1,
			"wildcard_filter": 0
		}
	]
};
