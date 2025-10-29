// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
  refresh: (frm) => {
    frm.set_query('package_unit', () => {
      return {
        filters: { is_packaging_unit: 1 }
      };
    });
	const read_only_fields = ['item_name', 'item_group', 'stock_uom', 'package_unit', 'origin_country', 'item_type', 'tax_type'];
	read_only_fields.forEach(field => {
		frm.set_df_property(field, 'read_only', frm.doc.__islocal ? 0 : 1);
	});
  }
});
