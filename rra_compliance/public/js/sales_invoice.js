// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
  refresh: async (frm) => {
	frm.set_df_property('taxes_and_charges', 'reqd', true);
	frm.set_query('item_code', 'items', () => {
	  return {
	    filters: { rra_pushed: 1, is_sales_item: 1 }
	  };
	});
	if (!frm.doc.taxes_and_charges) {
      const company_abbr = await frappe.db.get_value('Company', frm.doc.company, 'abbr');
	  frm.set_value('taxes_and_charges', `Rwanda Tax - ${company_abbr.message.abbr}`);
	}
  }
});
