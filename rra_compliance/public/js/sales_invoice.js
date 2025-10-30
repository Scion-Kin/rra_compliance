// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
  refresh: (frm) => {
	frm.set_query('item_code', 'items', () => {
	  return {
	    filters: { rra_pushed: 1, is_sales_item: 1 }
	  };
	});
  }
});
