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
				<th>Invoice</th>
				<th>Item</th>
				<th>Qty</th>
				<th>Price</th>
				<th>Tax</th>
				<th>Total</th>
				<th>Map to Item</th>
			</tr>
		</thead>
		<tbody>
	`;

	purchases.forEach(purchase => {
		// Invoice header row
		html += `
			<tr class="invoice-row">
				<td colspan="7">
					${purchase.spplrNm}
					<span class="badge">Invoice #${purchase.spplrInvcNo}</span>
					<span class="badge">TIN ${purchase.spplrTin}</span>
					<span class="badge">${purchase.cfmDt}</span>
				</td>
			</tr>
		`;

		// Item rows
		purchase.itemList.forEach(item => {
			html += `
				<tr class="item-row">
					<td>${purchase.spplrInvcNo}</td>
					<td>
						<strong>${item.itemNm}</strong><br>
						<small>${item.itemCd}</small>
					</td>
					<td>${item.qty} ${item.qtyUnitCd}</td>
					<td>${frappe.format(item.prc, { fieldtype: "Currency" })}</td>
					<td>${item.taxTyCd}</td>
					<td>${frappe.format(item.totAmt, { fieldtype: "Currency" })}</td>
					<td>
						<select 
							class="mapping-select"
							data-item-cd="${item.itemCd}"
						>
							<option value="">Select Item</option>
						</select>
					</td>
				</tr>
			`;
		});
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

frappe.ui.form.on('RRA Purchase Mapper', {
	refresh: function(frm) {
		frm.set_df_property('purchase_list', 'options', css + '<div id="purchase-list"></div>');
	},
	from_date: async function(frm) {
		frappe.dom.freeze('Loading purchases...');
		const purchase_list = await frappe.call({
			method: 'rra_compliance.main.get_purchases',
			args: { from_date: frm.doc.from_date, company: frm.doc.company }
		});
		frm.set_df_property('purchase_list', 'options', css + render_purchase_table(purchase_list.message));
		load_item_options();
		frappe.dom.unfreeze();
	}
});

$(document).on('change', '.mapping-select', function () {
	const external_item = this.dataset.itemCd;
	const internal_item = this.value;

	console.log({
		external_item,
		internal_item
	});
});
