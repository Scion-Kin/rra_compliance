import frappe


@frappe.whitelist()
def get_rra_invoice_html(doc_name: str) -> str:
    """
    Accepts doc (Sales Invoice) from print format
    Returns fully rendered HTML
    """

    doc = frappe.get_doc("Sales Invoice", doc_name)
    rra = frappe.get_doc("RRA Sales Invoice Log", {"sales_invoice": doc.name, "docstatus": 1, "rra_pushed": 1})

    if rra:
        frappe.db.set_value("RRA Sales Invoice Log", rra.name, "printed_count", (rra.get("printed_count") or 0) + 1)
    else:
        frappe.throw("<b>Entry not found for this Sales Invoice. Please ensure the invoice has been pushed to RRA and try again.</b>")

    company = frappe.get_doc("Company", doc.company)
    company_address = frappe.get_all("Address", filters={"is_your_company_address": 1})
    company_address = frappe.get_value("Dynamic Link", {"link_doctype": "Company", "parenttype": "Address", "parent": ['in', company_address]}, 'parent') \
		if company_address else None

    customer_tax_id = frappe.db.get_value("Customer", doc.customer, "tax_id")

    log = frappe.parse_json(rra.get("payload"))
    qr_data = f"{log.get('salesDt','')}#{log.get('cfmDt','')[8:]}#{rra.get('sdc_id','')}#" f"{rra.get('rcpt_no','')}#{rra.get('intrl_data','')}#{rra.get('rcpt_sign','')}"

    tax_groups = {}
    log_items = {item.get("itemCd"): item for item in log.get("itemList", [])}
    for item in doc.items:
        code = item.item_tax_template.split(" - ")[0]
        if code not in tax_groups:
            tax_groups[code] = 0

        log_item = log_items.get(item.item_code, {})
        tax_groups[code] += float(log_item.get("taxAmt", 0))

    html = frappe.render_template(
        "rra_compliance/rra_compliance/print_format/rra_sales_invoice/rra_sales_invoice.html",
        {
            "doc": doc,
            "company": company,
			"company_address": company_address,
            "customer_tax_id": customer_tax_id,
			"customer": doc.customer,
            "rra": rra,
            "log": log,
            "qr_data": qr_data,
            "tax_groups": tax_groups,
        },
    )

    return html

