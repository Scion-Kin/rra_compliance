// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
  refresh: (frm) => {
    frm.set_query('package_unit', () => {
      return {
        filters: { is_packaging_unit: 1 }
      };
    });
  }
});
