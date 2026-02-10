// Copyright (c) 2026 Buffer Punk Ltd. All Rights Reserved.

const css = `
<style>
.frappe-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  font-size: 13px;
}

.frappe-table th {
  background: #f7f7f7;
  border-bottom: 1px solid #d1d8dd;
  padding: 8px;
  text-align: left;
  font-weight: 600;
}

.frappe-table td {
  border-bottom: 1px solid #ebeef0;
  padding: 8px;
  vertical-align: top;
}

.frappe-table tr.invoice-row td {
  background: #fafbfc;
  font-weight: 600;
}

.frappe-table tr.item-row:hover {
  background: #f8f9fa;
}

.mapping-select {
  width: 100%;
  padding: 4px;
}
.badge {
  background: #e7f5ff;
  color: #1c7ed6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}
</style>
`;

function render_purchase_table(purchases) {
	let html = `
	<table class="frappe-table">
		<thead>
			<tr>
				<th>Sr No.</th>
				<th>Task Code</th>
				<th>Declaration Date</th>
				<th>Declaration Number</th>
				<th>Supplier's name</th>
				<th>Agent name</th>
				<th>Origin Country</th>
				<th>Item</th>
				<th>Map to Item</th>
				<th>Import Item Status</th>
			</tr>
		</thead>
		<tbody>
	`;

	itemList.forEach(item => {
		html += `
			<tr class="item-row">
				<td>${item.itemSeq}</td>
				<td>${item.taskCd}</td>
				<td>${frappe.format(item.dclDe, { fieldtype: "Date" })}</td>
				<td>${item.dclNo}</td>
				<td>${item.agntNm}</td>
				<td>${item.invcFcurAmt}</td>
				<td>${item.exptNatCd}</td>
				<td>
					<strong>${item.itemNm}</strong><br>
					<small>${item.hsCd}</small>
				</td>
				<td>
					<select 
						class="mapping-select"
						data-item-cd="${item.itemNm}"
					>
						<option value="">Select Item</option>
					</select>
				</td>
				<td>
					<select class="status-select" data-item-cd="${item.itemNm}">
						<option value="1">Unsent</option>
						<option value="2">Waiting</option>
						<option value="3" selected>Approved</option>
						<option value="4">Cancelled</option>
					</select>
				</td>
			</tr>
		`;
	});

	html += `</tbody></table>`;
	return html;
}

function load_item_options() {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Item',
			fields: ['name', 'item_name'],
			limit_page_length: 1000
		},
		callback: function(r) {
			const items = r.message || [];
			const options = items
				.map(i => `<option value="${i.name}">${i.item_name}</option>`)
				.join('');

			document.querySelectorAll('.mapping-select').forEach(select => {
				select.insertAdjacentHTML('beforeend', options);
			});
		}
	});
}

let itemList = [];
frappe.ui.form.on('RRA Import Items', {
	refresh: function(frm) {
		frm.disable_save();
		frm.set_df_property('purchase_list', 'options', css + '<div id="purchase-list"></div>');
		frm.set_value('from_date', '');
	},
	from_date: async function(frm) {
		frm.page.set_primary_action(__('Get Imported Items'), async function() {
			frappe.dom.freeze('Getting imported items...');
			itemList = await frappe.call({
				method: 'rra_compliance.main.get_imported_items',
				args: { from_date: frm.doc.from_date, company: frm.doc.company }
			});

			itemList = itemList.message || [];
			frm.set_df_property('purchase_list', 'options', css + render_purchase_table(itemList));
			load_item_options();
			frappe.dom.unfreeze();

			frm.page.set_primary_action(__('Save Imported Items'), async () => {
				frappe.dom.freeze('Saving mapped items...');
				const mappings = {};
				document.querySelectorAll('.mapping-select').forEach(select => {
					const item_cd = select.dataset.itemNm;
					const mapped_item = select.value;
					if (mapped_item) {
						mappings[item_cd] = { mapped_item };
					}
				});

				document.querySelectorAll('.status-select').forEach(select => {
					const item_cd = select.dataset.itemNm;
					const status = select.value;
					if (mappings[item_cd]) {
						mappings[item_cd].status = status;
					}
				});

				console.log('Saving mappings:', mappings);
				itemList.forEach(item => {
					if (mappings[item.itemNm]) {
						item.itemNm = mappings[item.itemNm];
					} else {
						frappe.dom.unfreeze();
						frappe.throw('Please map all items before saving.');
					}
				});
				try {
					const message = await frappe.call({
						method: 'rra_compliance.main.update_imported_items',
						args: { itemList, company: frm.doc.company }
					});
					frappe.dom.unfreeze();
					frappe.msgprint(message.message);
				} catch (error) {
					frappe.msgprint('Error saving purchases: ' + error?.message || error);
				} finally {
					frm.page.clear_primary_action();
					frm.set_df_property('purchase_list', 'options', css + '<div id="purchase-list"></div>');
				}
			});
		});
	},
});
