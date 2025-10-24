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
		frm.set_value('item_name', '');
		frm.set_df_property('item_code', 'readonly', true);
		frm.set_df_property('item_code', 'required', false);
		frm.set_df_property('stock_uom', 'default', '');
	}
  },
  before_save: async (frm) => {
	if (frm.doc.__islocal) {
		frappe.call({
			method: 'rra_compliance.rra_compliance.doctype.item.item.generate_rra_item_code',
			args: {
				self: {
					origin_country: frm.doc.origin_country,
					item_type: frm.doc.item_type,
					package_unit: frm.doc.package_unit,
					stock_uom: frm.doc.stock_uom,
				}
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value('item_code', r.message);
					frm.refresh_field('item_code');
				}
			}
		});
	}
  }
});

