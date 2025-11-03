import frappe

def update_amendment_settings(action="make"):
	"""
		This is to prevent frappe from automatically adding a suffix on amended documents.
	"""
	doctypes = [
		"RRA Sales Invoice Log",
		# Others will be added later as project grows
	]
	settings = frappe.get_single("Document Naming Settings")
	for doctype in doctypes:
		e = next((item for item in settings.amend_naming_override if item.document_type == doctype), None)
		if e is None:
			if action == "make":
				settings.append("amend_naming_override", {"document_type": doctype, "action": "Default Naming"})
		else:
			if action == "make":
				e.action = "Default Naming"
			else:
				settings.amend_naming_override.pop(e.idx)

	settings.save()

