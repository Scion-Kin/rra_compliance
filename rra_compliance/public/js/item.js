// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
  refresh: (frm) => {
    frm.set_query('stock_uom', () => {
      return {
		filters: { uom_name: ['like', '% - QU'] }
      };
    });
    frm.set_query('package_unit', () => {
      return {
		filters: { uom_name: ['like', '% - PU'] }
      };
    });
	const read_only_fields = ['item_name', 'item_group', 'stock_uom', 'package_unit', 'origin_country', 'item_type', 'tax_type'];
	if (!frm.doc.__islocal)
		read_only_fields.forEach(field => {
			frm.set_df_property(field, 'read_only', 1);
		});
  }
});
