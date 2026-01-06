// Copyright (c) 2025, Buffer Punk and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item', {
  refresh: (frm) => {
	if (!frm.doc.rra_initialized)
		frm.add_custom_button(__('Initialize RRA'), function () {
			if (!frm.doc.branch_id || !frm.doc.tax_id) {
				frappe.throw(
					__('Please set the Branch ID and Tax ID before initializing.')
				);
			}
			frappe.prompt({
				label: 'Device Serial Number',
				fieldname: 'device_id',
				fieldtype: 'Data',
				reqd: 1
			}, function (data) {
				frappe.call({
					method: 'rra_compliance.main.initialize_company',
					args: {
						dvcSrlNo: data.device_id,
						company: frm.doc.name
					},
					callback: function (response) {
						if (response.message) {
							frappe.msgprint(__(response.message));
						}
						frm.reload_doc();
					}
				});
			});
		}, __('Manage'));
  },
});
