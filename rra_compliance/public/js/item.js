// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
  refresh: (frm) => {
    frm.set_query('package_unit', () => {
      return {
        filters: { is_packaging_unit: 1 }
      };
    });
	if (frm.doc.__islocal) {
		frm.set_value('item_code', 'temp');
		// hide the field as the name will be generated from the backend
		frm.set_df_property('item_code', 'hidden', true);
	}
  }
});

