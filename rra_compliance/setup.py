from click import progressbar
from datetime import datetime
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from rra_compliance.utils.rra_frappe_translation import rra_to_frappe, to_replace
from rra_compliance.utils.naming_settings import update_amendment_settings
from rra_compliance.utils.functions import shorten_string

import frappe
import requests
import json
"""
	Note:
		RRA transactions are a mess — there's no standard naming convention at all.
		Most of the time, we end up hardcoding values until we can figure out a more stable approach.
		Their API design is awful: payloads are inconsistent, poorly documented, and confusing to integrate with.
		Everything about this process is a nightmare, but compliance is mandatory.
		So, if you're reading this later — sorry for the mess. We did our best to keep it clean and sane.

	Note 2:
		The payloads expected by RRA are large, with many unnecessary fields, required and redundant.
		We only send the required fields to keep things simple.
"""


class RRAComplianceFactory:
	def __init__(self, tin=None, bhf_id=None, base_url=None):
		settings = frappe.get_doc("RRA Settings")

		if base_url:
			settings.update({
				"base_url": base_url,
				"tin": tin,
				"bhfid": bhf_id,
			})
			settings.save(ignore_permissions=True)

		self.BASE_URL = base_url or settings.get('base_url')
		self.BASE_PAYLOAD = {
			"tin": tin or settings.get('tin'),
			"bhfId": bhf_id or settings.get('bhfid'),
		}
		self.endpoints = {
			"initialize": "/initializer/selectInitInfo", # Done
			"get_codes": "/code/selectCodes", # Done
			"get_item_class": "/itemClass/selectItemsClass", # Done
			"get_customer": "/customers/selectCustomer", # Done
			"get_branches": "/branches/selectBranches", # Done
			"get_notices": "/notices/selectNotices",
			"update_branch_customers": "/branches/saveBrancheCustomers",
			"update_branch_users": "/branches/saveBrancheUsers",
			"update_branch_insurances": "/branches/saveBrancheInsurances",
			"get_items": "/items/selectItems",
			"push_item": "/items/saveItems", # Done
			"save_item_composition": "/items/saveItemComposition",
			"get_imported_items": "/imports/selectImportItems",
			"update_imported_items": "/imports/updateImportItems",
			"save_sale": "/trnsSales/saveSales", # Done
			"get_purchases": "/trnsPurchase/selectTrnsPurchaseSales",
			"save_purchase": "/trnsPurchase/savePurchases",
			"update_stock": "/stockMaster/saveStockMaster",
			"get_stock_items": "/stock/selectStockItems",
			"update_stock_items": "/saveStockItems/saveStockItems"
		}

	def run_after_init(self, action="make"):
		methods = ['get_item_class', 'get_branches', 'get_items', 'get_purchases']
		for method in methods:
			try:
				getattr(self, method)(action=action)
			except Exception as e:
				print(f"Error executing {method}: {e}")

	def get_url(self, endpoint):
		return f"{self.BASE_URL}{endpoint}"

	def get_payload(self, **kwargs):
		payload = self.BASE_PAYLOAD.copy()
		payload.update(kwargs)
		return payload

	def initialize(self, action="make"):
		""" Initialize connection with RRA and fetch taxpayer and branch details """
		url = self.get_url(self.endpoints["initialize"])
		dvcSrlNo = input("Enter Device Serial No: ").strip()
		response_data = self.next(requests.post(url, json=self.get_payload(dvcSrlNo=dvcSrlNo)), print_if='any', print_to='stdout').get("data", {}).get("info", {})
		if action == "make":
			company = frappe.get_doc("Company", frappe.defaults.get_global_default("company")).update({ "tax_id": self.BASE_PAYLOAD.get("tin") })
			company.save()
			if not response_data:
				return
			existing_doc = frappe.get_doc("RRA Settings")
			for field in response_data.keys():
				setattr(existing_doc, field.lower(), response_data.get(field))

			existing_doc.update({"hqyn": 1 if response_data.get("hqYn") == "Y" else 0})
			existing_doc.save(ignore_permissions=True)
			print(f"\n\033[92mSUCCESS \033[0mRRA Settings updated for TIN: {response_data.get('tin')}.\n")

	def get_codes(self, action="make"):
		""" Get codes from RRA and dump them into respective doctypes """
		url = self.get_url(self.endpoints["get_codes"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("clsList", [])
		if response_data:
			for item, _ in to_replace.items():
				try:
					docs = frappe.get_all(item, fields=["name"])
					with progressbar(length=len(docs), empty_char=" ", fill_char="=", label="Syncing transaction codes", show_pos=True, item_show_func=lambda x: x) as bar:
						for doc in docs:
							frappe.delete_doc(item, doc.name, ignore_permissions=True, force=True)
							bar.update(1, f"Deleted {item} : {doc.name}")

					frappe.db.commit()
					print(f"\n\033[92mSUCCESS \033[0mAll existing {item} records deleted.\n")
				except Exception as e:
					print(f"Could not delete existing {item} records: {e}")

			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing transaction codes", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					try:
						doc = frappe.get_doc({
							"doctype": "RRA Transaction Codes",
							"cdcls": item.get("cdCls"),
							"cdclsnm": item.get("cdClsNm").strip(),
							"cdclsdesc": item.get("cdClsDesc"),
							"useyn": 1 if item.get("useYn") == "Y" else 0,
							"relation": rra_to_frappe.get(item.get("cdClsNm")),
							"userdfnnm1": item.get("userDfnNm1"),
							"userdfnnm2": item.get("userDfnNm2"),
							"userdfnnm3": item.get("userDfnNm3"),
							"docstatus": 1
						})
						if action == "make":
							if not frappe.db.exists("RRA Transaction Codes", item.get("cdClsNm")):
								for i in item.get("dtlList", []):
									doc.append("items", {
										"cd": i.get("cd"),
										"cdnm": i.get("cdNm").strip(),
										"cddesc": i.get("cdDesc"),
										"useyn": 1 if i.get("useYn") == "Y" else 0,
										"srtord": i.get("srtOrd"),
										"userdfn1": i.get("userDfn1"),
										"userdfn2": i.get("userDfn2"),
										"userdfn3": i.get("userDfn3"),
									})
									new_item_setting = to_replace.get(rra_to_frappe.get(item.get("cdClsNm")))
									if new_item_setting:
										try:
											frappe.get_doc({
												"doctype": rra_to_frappe.get(item.get("cdClsNm")),
												**({ key: i.get(value) if not isinstance(value, dict) else eval(value.get('eval')) for key, value in new_item_setting.items() })
											}).insert(ignore_permissions=True)
										except Exception:
											pass

								doc.insert(ignore_permissions=True)
								bar.update(1, f"Created Code: {item.get('cdCls')} - {item.get('cdClsNm')}")

						elif action == "destroy":
								doc.delete()
								bar.update(1, f"Deleted Code: {item.get('cdCls')} - {item.get('cdClsNm')}")
					except Exception as e:
						bar.update(1, f"Could not process code {item.get('cdCls')}: {e}")

					frappe.db.commit()

			print("\n\033[92mSUCCESS \033[0mCodes synchronization completed.")
		else:
			print("No codes found in the response.\n")

	def get_item_class(self, action="make"):
		""" Get items classes from RRA and dump them into item group """
		url = self.get_url(self.endpoints["get_item_class"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("itemClsList", [])
		if response_data:
			existing_docs = frappe.get_all("Item Group", fields=["name"])
			with progressbar(length=len(existing_docs), empty_char=" ", fill_char="=", label="Deleting existing item groups", show_pos=True, item_show_func=lambda x: x) as bar:
				for doc in existing_docs:
					# frappe.delete_doc("Item Group", doc.name, ignore_permissions=True, force=True)
					# Uncomment the quote above to enable deletion of existing item groups.
					# Deletion takes an awfully long time and I'm commenting to speed up testing.
					# frappe.db.commit()
					bar.update(1, f"Deleted Item Group: {doc.name}")

			print("\n\033[92mSUCCESS \033[0mAll existing Item Group records deleted. Inserting new records...\n")

			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing item groups", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					try:
						doc = frappe.get_doc({
							"doctype": "Item Group",
							"item_group_name": item.get("itemClsNm").strip(),
							"itemclscd": item.get("itemClsCd"),
							"itemclslvl": item.get("itemClsLvl"),
							"taxtycd": item.get("taxTyCd"),
							"mjrtgyn": 1 if item.get("mjrTgYn") == "Y" else 0,
							"useyn": 1 if item.get("useYn") == "Y" else 0,
						})
						if action == "make":
							if not frappe.db.exists("Item Group", item.get("itemClsNm")):
								doc.insert(ignore_permissions=True)
								bar.update(1, f"Created Item Group: {item.get('itemClsCd')} - {item.get('itemClsNm')}")
							else:
								existing_doc = frappe.get_doc("Item Group", item.get("itemClsNm"))
								existing_doc.update({
									"itemclscd": item.get("itemClsCd"),
									"itemclslvl": item.get("itemClsLvl"),
									"taxtycd": item.get("taxTyCd"),
									"mjrtgyn": 1 if item.get("mjrTgYn") == "Y" else 0,
									"useyn": 1 if item.get("useYn") == "Y" else 0
								})
								existing_doc.save(ignore_permissions=True)
								bar.update(1, f"Updated Item Group: {item.get('itemClsCd')} - {item.get('itemClsNm')}")

						elif action == "destroy":
								doc.delete()
								bar.update(1, f"Deleted Item Group: {item.get('itemClsCd')} - {item.get('itemClsNm')}")
					except Exception as e:
						bar.update(1, f"Could not process item group {item.get('itemClsCd')}: {e}")

					frappe.db.commit()

				print("\n\033[92mSUCCESS \033[0mItem Categories synchronization completed.")
		else:
			print("No item classes found in the response.\n")

	def get_customer(self, customer_tin, action="make"):
		""" Get customers from RRA and dump them into customer doctype """
		url = self.get_url(self.endpoints["get_customer"])
		response_data = self.next(requests.post(url, json=self.get_payload(custmTin=customer_tin))).get("data", {}).get("custList", [])
		if response_data:
			item = response_data[0]
			try:
				doc = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": item.get("taxprnm"),
					"tax_id": customer_tin,
					"taxprsttscd": item.get("taxPrSttsCd"),
				})
				if action == "make":
					if not frappe.db.exists("Customer", item.get("custNm")):
						doc.insert(ignore_permissions=True)
					else:
						existing_doc = frappe.get_doc("Customer", item.get("custNm"))
						existing_doc.update({
							"customer_name": item.get("taxprnm"),
							"tax_id": customer_tin,
							"taxprsttscd": item.get("taxPrSttsCd"),
						})
						existing_doc.save(ignore_permissions=True)

				elif action == "destroy":
					doc.delete()
			except Exception as e:
				print(f"Could not delete customer {item.get('custNm')}: {e}")

	def get_branches(self, action="make"):
		""" Get branches from RRA and dump them into branch doctype """
		url = self.get_url(self.endpoints["get_branches"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("bhfList", [])
		if response_data:
			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing branches", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					try:
						doc = frappe.get_doc({
							"doctype": "Branch",
							"branch": item.get("brnchNm").strip(),
							"bhfid": item.get("bhfId"),
							"bhfsttscd": item.get("bhfSttsCd"),
							"prvncnm": item.get("prvncNm"),
							"dstrtnm": item.get("dstrtNm"),
							"sctrnm": item.get("sctrNm"),
							"locdesc": item.get("locDesc"),
							"mgrnm": item.get("mgrNm"),
							"mgrtelno": item.get("mgrTelNo"),
							"mgremail": item.get("mgrEmail"),
							"hqyn": 1 if item.get("hqYn") == "Y" else 0,
						})
						if action == "make":
							if not frappe.db.exists("Branch", item.get("brnchNm")):
								doc.insert(ignore_permissions=True)
								bar.update(1, f"Created Branch: {item.get('bhfId')} - {item.get('brnchNm')}")
							else:
								existing_doc = frappe.get_doc("Branch", item.get("brnchNm"))
								existing_doc.update({
									"bhfid": item.get("bhfId"),
									"bhfsttscd": item.get("bhfSttsCd"),
									"prvncnm": item.get("prvncNm"),
									"dstrtnm": item.get("dstrtNm"),
									"sctrnm": item.get("sctrNm"),
									"locdesc": item.get("locDesc"),
									"mgrnm": item.get("mgrNm"),
									"mgrtelno": item.get("mgrTelNo"),
									"mgremail": item.get("mgrEmail"),
									"hqyn": 1 if item.get("hqYn") == "Y" else 0,
								})
								existing_doc.save(ignore_permissions=True)
								bar.update(1, f"Updated Branch: {item.get('bhfId')} - {item.get('brnchNm')}")

						elif action == "destroy":
								doc.delete()
								bar.update(1, f"Deleted Branch: {item.get('bhfId')} - {item.get('brnchNm')}")
					except Exception as e:
						bar.update(1, f"Could not process branch {item.get('bhfId')}: {e}")

			print("\n\033[92mSUCCESS \033[0mBranches synchronization completed.")

	def get_notices(self, date: datetime = datetime(2018, 5, 20)):
		url = self.get_url(self.endpoints['get_notices'])
		payload = self.get_payload(lastReqDt=date.strftime("%Y%m%d%H%M%S"))
		return self.next(requests.post(url, json=payload))

	def get_items(self, last_request_date: datetime = datetime(2018, 5, 20), action="make"):
		"""
			Get items from RRA and dump them into Item doctype.
			This method is not yet implemented.
		"""
		url = self.get_url(self.endpoints['get_items'])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt=last_request_date.strftime("%Y%m%d%H%M%S")))).get('data', {}).get('itemList', [])
		if response_data:
			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing items", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					try:
						doc = frappe.get_doc({
							"doctype": "Item",
							"item_code": item.get("itemCd"),
							"item_name": item.get("itemNm").strip(),
							"item_group": frappe.db.get_value("Item Group", {"itemclscd": item.get("itemClsCd")}, "item_group_name"),
							"item_type": item.get("itemTyCd"),
							"origin_country": item.get("orgnNatCd"),
							"quantity_unit": item.get("qtyUnitCd"),
							"tax_type": item.get("taxTyCd"),
							"rra_pushed": 1,
							"disabled": 0 if item.get("useYn") == "Y" else 1,
						})
						if action == "make":
							if not frappe.db.exists("Item", item.get("itemCd")):
								doc.insert(ignore_permissions=True)
								bar.update(1, f"Created Item: {item.get('itemCd')} - {item.get('itemNm')}")
							else:
								existing_doc = frappe.get_doc("Item", item.get("itemCd"))
								existing_doc.update({
									"item_name": item.get("itemNm"),
									"item_group": frappe.db.get_value("Item Group", {"itemclscd": item.get("itemClsCd")}, "item_group_name"),
									"item_type": item.get("itemTyCd"),
									"origin_country": item.get("orgnNatCd"),
									"quantity_unit": item.get("qtyUnitCd"),
									"tax_type": item.get("taxTyCd"),
									"rra_pushed": 1,
									"disabled": 0 if item.get("useYn") == "Y" else 1,
								})
								existing_doc.save(ignore_permissions=True)
								bar.update(1, f"Updated Item: {item.get('itemCd')} - {item.get('itemNm')}")
						elif action == "destroy":
								doc.delete()
								bar.update(1, f"Deleted Item: {item.get('itemCd')} - {item.get('itemNm')}")
					except Exception as e:
						bar.update(1, f"Could not process item {item.get('itemCd')}: {e}")

			print("\n\033[92mSUCCESS \033[0mItems synchronization completed.")
		else:
			print("No items found in the response.\n")

	def get_purchases(self, date: datetime = datetime(2018, 5, 20), action: str = "make"):
		"""
			Get purchases from RRA.
			:param date: Date from which to fetch purchases
			:return: None
		"""
		if action != "make":
			return # We cannot delete purchases as they are submitted documents.

		url = self.get_url(self.endpoints['get_purchases'])
		payload = self.get_payload(lastReqDt=date.strftime("%Y%m%d%H%M%S"))
		response_data = self.next(requests.post(url, json=payload)).get("data", []).get("saleList", [])
		with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Fetching purchases", show_pos=True, item_show_func=lambda x: x) as bar:
			for purchase in response_data:
				try:
					supplier = frappe.get_value("Supplier", { "supplier_name": purchase.get("spplrNm") }, "name")
					if not supplier:
						supplier = frappe.get_doc({
							"doctype": "Supplier",
							"supplier_name": purchase.get("spplrNm"),
							"tax_id": purchase.get("spplrTin"),
							"branch_id": purchase.get("spplrBhfId"),
						}).insert(ignore_permissions=True).name

					purchase_doc = frappe.get_doc({
						"doctype": "Purchase Invoice",
						"supplier": supplier,
						"bill_no": purchase.get("spplrInvcNo"),
						"sdc_id": purchase.get("sdcId"),
						"posting_time": datetime.strptime(purchase.get("cfmDt"), "%Y-%m-%d %H:%M:%S").time(),
						"posting_date": datetime.strptime(purchase.get("salesDt"), "%Y%m%d").date(),
						"bill_date": datetime.strptime(purchase.get("salesDt"), "%Y%m%d").date(),
						"mode_of_payment": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Payment Type", "cd": purchase.get("pmtTyCd") }, 'cdnm'),
						"paid_amount": purchase.get("totAmt"),
						"is_paid": 1,
					})
					purchase_doc.cash_bank_account = get_bank_cash_account(purchase_doc.mode_of_payment, purchase_doc.company).get("account")
					log = frappe.get_doc({
						"doctype": "RRA Purchase Invoice Log",
						"docstatus": 1,
						"invc_no": int(frappe.get_value("RRA Purchase Invoice Log", {"rra_pushed": 1}, "invc_no") or 0) + 1,
						"rra_pushed": 1,
						"payload": json.dumps(purchase),
					})

					for item in purchase.get("itemList", []):
						if not frappe.db.exists("Item", item.get("itemCd")):
							new_item = frappe.get_doc({
								"doctype": "Item",
								"item_code": item.get("itemCd"),
								"item_name": item.get("itemNm"),
								"item_group": frappe.db.get_value("Item Group", {"itemclscd": item.get("itemClsCd")}, "item_group_name"),
								"stock_uom": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Quantity Unit", "cd": item.get("qtyUnitCd") }, 'cdnm'),
								"package_unit": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Packing Unit", "cd": item.get("pkgUnitCd") }, 'cdnm'),
								"origin_country": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Cuntry", "cd": item.get("itemCd")[:2] }, 'cdnm'),
								"item_type": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Item Type", "cd": item.get("itemCd")[2] }, 'cdnm'),
								"tax_type": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Taxation Type", "cd": item.get("taxTyCd") }, 'cdnm'),
								"rra_pushed": 1,
							})
							new_item.taxes = []
							new_item.append("taxes", {
								 "item_tax_template": frappe.get_last_doc("Item Tax Template", filters={"title": new_item.tax_type}).name
							})
							new_item.insert(ignore_permissions=True)

						purchase_doc.append("items", {
							"item_code": item.get("itemCd"),
							"item_name": item.get("itemNm"),
							"qty": item.get("qty"),
							"rate": item.get("prc"),
							"base_rate": item.get("prc"),
						})

					purchase_doc.insert()
					log.update({ "purchase_invoice": purchase_doc.name })
					log.insert()
					purchase_doc.submit()
					bar.update(1, f"Inserted purchase from {purchase.get('spplrNm')}")

				except Exception as e:
					bar.update(1, f"Could not process purchase from {purchase.get('spplrNm')}: {e}")

		print(f"\n\033[92m{action.capitalize()} SUCCESS \033[0mPurchases synchronization completed.")

	def push_item(self, item_code: str):
		"""
			Push item to RRA.
		"""
		url = self.get_url(self.endpoints['push_item'])
		doc = frappe.get_doc("Item", item_code)
		payload = self.get_payload(**{
			"itemCd": doc.get('item_code'),
			"itemClsCd": doc.get('itemclscd'),
			"itemNm": doc.get('item_name'),
			"dftPrc": doc.get("valuation_rate") or 0,
			"itemTyCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Item Type", "cdnm": doc.get('item_type') }, 'cd'),
			"orgnNatCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Cuntry", "cdnm": doc.get('origin_country') }, 'cd'),
			"pkgUnitCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Packing Unit", "cdnm": doc.get('package_unit') }, 'cd'),
			"qtyUnitCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Quantity Unit", "cdnm": doc.get('stock_uom') }, 'cd'),
			"taxTyCd": frappe.get_value("RRA Transaction Codes Item", {"parent" : "Taxation Type", "cdnm": doc.get('tax_type') }, 'cd'),
			"isrcAplcbYn": "Y" if doc.get('isrc_applicable') else "N",
			"useYn": "N" if doc.get('disabled') else "Y",
			"regrNm": "Admin",
			"regrId": "Admin",
			"modrNm": "Admin",
			"modrId": "Admin"
		})
		response = self.next(requests.post(url, json=payload), print_if='fail', print_to='frappe')
		if response.get("resultCd") == "000":
			doc.rra_pushed = 1
		else:
			frappe.msgprint(
				msg=f"Failed to push item {doc.get('item_code')} to RRA. An hourly retry will be attempted in the background.",
				indicator="red"
			)
			frappe.enqueue(self.push_item, item_code=item_code, queue='long', timeout=1500)

		doc.taxes = []
		doc.append("taxes", {
			 "item_tax_template": frappe.get_last_doc("Item Tax Template", filters={"title": doc.tax_type}).name
		})
		doc.save(ignore_permissions=True)

	def save_sale(self, sales_invoice_id: str):
		"""
			Save sales to RRA.
			:param sales_invoice_id: Sales Invoice ID
			:return: None
			Note:
				Don't worry about Pyright and Ruff complaints. They can't understand dynamic typing and complex structures.
		"""
		url = self.get_url(self.endpoints['save_sale'])
		sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_id)
		if len(sales_invoice.taxes) == 0:
			frappe.throw("Please apply taxes to the Sales Invoice before submitting.")

		customer = frappe.get_doc("Customer", sales_invoice.customer)
		last_log = None
		new_invoc_no = 1
		try:
			last_log = frappe.get_last_doc("RRA Sales Invoice Log", filters={"sales_invoice": sales_invoice_id}, order_by="invc_no desc")
			last_in = frappe.get_last_doc("RRA Sales Invoice Log", order_by="invc_no desc")
			new_invoc_no = int(last_in.invc_no) + 1
		except Exception:
			pass

		if last_log and last_log.docstatus == 1:
			last_log.cancel()

		items = { i.item_code: frappe.get_value("Item Tax Template", i.item_tax_template, "title") for i in sales_invoice.items }
		tax_rates = {
			template.title: frappe.get_value("Item Tax Template Detail", { "parent": template.name, "tax_type": frappe.get_last_doc("Account", filters={"name": ["like", "VAT - %"]}).name }, "tax_rate")
			for template in frappe.get_all("Item Tax Template", fields=["title", "name"])
		}
		tax_amounts = { key: val[1] for key, val in json.loads(sales_invoice.taxes[0].item_wise_tax_detail).items() }
		date = datetime.strptime(f"{sales_invoice.posting_date} {sales_invoice.posting_time}", "%Y-%m-%d %H:%M:%S.%f")

		payload = self.get_payload(**{
			"salesDt": date.strftime("%Y%m%d"),
			"cfmDt": date.strftime("%Y%m%d%H%M%S"),
			"invcNo": new_invoc_no,
			"rptNo": new_invoc_no,
			"orgInvcNo": frappe.get_value("RRA Sales Invoice Log", {
				"sales_invoice": sales_invoice.return_against,
				"rra_pushed": 1
			}, 'invc_no') if sales_invoice.is_return else 0,
			# Don't remove the above, else you'll suffer.
			**({"custTin": customer.tax_id} if customer.tax_id else {}),
			"custNm": customer.customer_name,
			"salesTyCd": "N", # Normal Sale. RRA supports other types but only wants "N"... for now??? forever??? ... We'll see.
			"rcptTyCd": frappe.get_value("RRA Transaction Codes Item", {
				"parent" : "Sales Receipt Type",
				"cdnm": "Refund after Sale" if sales_invoice.is_return else "Sale"
			}, 'cd'),
			"pmtTyCd": frappe.get_value("RRA Transaction Codes Item", {
				"parent" : "Payment Type",
				"cdnm": sales_invoice.get('payment_method') or "CASH"
			}, 'cd'),
			"salesSttsCd": "02" if sales_invoice.is_return else "05", # Approved / Refunded. We don't submit if not approved, to avoid complications.
			**{ f"taxblAmt{key[0][0]}":
				f"{sum(item.base_net_amount + tax_amounts.get(item.item_code, 0) for item in sales_invoice.items
					if items.get(item.item_code) == key[0]):.2f}" for key in tax_rates.items()
			},
			**{ f"taxRt{key[0]}": f"{value:.2f}" for key, value in tax_rates.items() },
			**{ f"taxAmt{key[0][0]}": f"{sum(tax_amounts.get(item.item_code, 0) for item in sales_invoice.items
				if items.get(item.item_code) == key[0]):.2f}" for key in tax_rates.items()
			},
			"totTaxblAmt": f"{sales_invoice.base_grand_total:.2f}",
			"totTaxAmt": f"{sales_invoice.base_total_taxes_and_charges:.2f}",
			"totAmt": f"{sales_invoice.base_grand_total:.2f}",
			"prchrAcptcYn": "Y" if not sales_invoice.is_return else "N",
			**({"rfdDt": date.strftime("%Y%m%d%H%M%S"), "rfdRsnCd": "03"} if sales_invoice.is_return else {}),
			"regrNm": shorten_string(sales_invoice.owner, 60),
			"regrId": shorten_string(sales_invoice.owner, 20),
			"modrNm": shorten_string(sales_invoice.modified_by, 60),
			"modrId": shorten_string(sales_invoice.modified_by, 20),
			"totItemCnt": len(sales_invoice.items),
			"itemList": [
				{
					"itemSeq": item.idx,
					"itemCd": item.item_code,
					"itemClsCd": frappe.get_value("Item", item.item_code, "itemclscd"),
					"itemNm": item.item_name,
					"pkgUnitCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Packing Unit", "cdnm": frappe.get_value("Item", item.item_code, "package_unit") }, 'cd'),
					"qtyUnitCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Quantity Unit", "cdnm": item.uom }, 'cd'),
					"qty": int(item.qty),
					"pkg": int(item.qty), # Bad API design. They want the quantity in both "pkg" and "qty".
					"prc": f"{item.base_net_rate + (tax_amounts.get(item.item_code, 0) / item.qty):.2f}",
					"splyAmt": f"{item.base_net_amount + tax_amounts.get(item.item_code, 0):.2f}", # Bad API design. They want both "splyAmt" and "totAmt".
					"dcRt": f"{item.discount_percentage:.2f}",
					"dcAmt": f"{item.discount_amount:.2f}",
					"taxTyCd": frappe.get_value("RRA Transaction Codes Item", {"parent" : "Taxation Type", "cdnm": items.get(item.item_code) }, 'cd'),
					"taxblAmt": f"{item.base_net_amount + tax_amounts.get(item.item_code, 0):.2f}",
					"totAmt": f"{item.base_net_amount + tax_amounts.get(item.item_code, 0):.2f}",
					"taxAmt": f"{tax_amounts.get(item.item_code, 0):.2f}", # This is not in the documentation but seems required.
				} for item in sales_invoice.items
			]
		})

		log = frappe.get_doc({
			"doctype": "RRA Sales Invoice Log",
			"sales_invoice": sales_invoice_id,
			"invc_no": payload.get("invcNo"),
			"payload": json.dumps(payload),
			"docstatus": 1,
			**({"amended_from": last_log.name} if last_log else {})
		})

		res = self.next(requests.post(url, json=payload), print_if='fail', print_to='frappe')
		if (res.get("resultCd") == "000"):
			log.update({
				"rra_pushed": 1,
				"intrl_data": res["data"].get("intrlData"),
				"rcpt_sign": res["data"].get("rcptSign"),
				"vsdc_rcpt_pbct_date": res["data"].get("vsdcRcptPbctDate"),
				"sdc_id": res["data"].get("sdcId"),
				"rcpt_no": res["data"].get("rcptNo"),
				"tot_rcpt_no": res["data"].get("totRcptNo"),
				"mrc_no": res["data"].get("mrcNo"),
			})
			log.save()
			frappe.msgprint(
				alert=True,
				msg=f"Sales Invoice successfully submitted to RRA with Invoice No: {log.invc_no}",
				indicator="green"
			)
		elif (res.get("resultCd") == "924"):  # 924 = Duplicate Entry
			"""
				Recursive until it finds a non-duplicate invoice number.
				This is necessary because RRA provides no way to check for existing invoice numbers
				... Like I said, their API design is awful.
			"""
			log.update({ "error": json.dumps(res), "rra_pushed": 1})
			log.save()
			try:
				self.save_sale(sales_invoice_id=sales_invoice_id)
			except RecursionError:
				frappe.throw("Maximum retries reached while trying to submit sales invoice to RRA. Please contact support.")
		else:
			log.update({ "error": json.dumps(res) })
			log.save()
			frappe.log_error(message=json.dumps(payload), title="RRA Sale Submission Failed")
			frappe.msgprint(
				msg="Failed to submit Sales Invoice to RRA. An hourly retry will be attempted in the background.",
				indicator="red"
			)

	def save_purchase(self, purchase_invoice_id: str):
		"""
			Save purchase to RRA.
			:param purchase_invoice_id: Purchase Invoice ID
			:return: None
		"""
		url = self.get_url(self.endpoints['save_purchase'])
		purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice_id)
		supplier = frappe.get_doc("Supplier", purchase_invoice.supplier)
		last_log = None
		new_invoc_no = 1
		try:
			last_log = frappe.get_last_doc("RRA Purchase Invoice Log", filters={"purchase_invoice": purchase_invoice_id}, order_by="invc_no desc")
			last_in = frappe.get_last_doc("RRA Purchase Invoice Log", order_by="invc_no desc")
			new_invoc_no = int(last_in.invc_no) + 1
		except Exception:
			pass

		if last_log and last_log.docstatus == 1:
			last_log.cancel()

		items = { i.item_code: frappe.get_value("Item Tax Template", i.item_tax_template, "title") for i in purchase_invoice.items }
		tax_rates = {
			template.title: frappe.get_value("Item Tax Template Detail", { "parent": template.name, "tax_type": frappe.get_last_doc("Account", filters={"name": ["like", "VAT - %"]}).name }, "tax_rate")
			for template in frappe.get_all("Item Tax Template", fields=["title", "name"])
		}
		tax_amounts = { key: val[1] for key, val in json.loads(purchase_invoice.taxes[0].item_wise_tax_detail).items() }
		date = datetime.strptime(f"{purchase_invoice.posting_date} {purchase_invoice.posting_time}", "%Y-%m-%d %H:%M:%S.%f")
		payload = self.get_payload(**{
			"invcNo": new_invoc_no,
			"cfmDt": date.strftime("%Y%m%d%H%M%S"),
			"pchsDt": date.strftime("%Y%m%d"),
			"wrhsDt": date.strftime("%Y%m%d%H%M%S"),
			**({"supplrTin": supplier.tax_id} if supplier.tax_id else {}),
			"supplrNm": supplier.supplier_name,
			"orgInvcNo": 0 if not purchase_invoice.is_return else frappe.get_value("RRA Purchase Invoice Log", {
				"purchase_invoice": purchase_invoice.return_against, "rra_pushed": 1, "docstatus": 1
			}, 'invc_no'),
			**({"spplrBhfId": supplier.get("branch_id")} if supplier.get("branch_id") else {}),
			**({"spplrInvcNo": purchase_invoice.bill_no} if purchase_invoice.bill_no else {}),
			**({"spplrSdcId": purchase_invoice.get("sdc_id")} if purchase_invoice.get("sdc_id") else {}),
			"regTyCd": "M",
			"pchsTyCd": "N",
			"rcptTyCd": frappe.get_value("RRA Transaction Codes Item", {
				"parent" : "Purchase Receipt Type",
				"cdnm": "Return after Purchase" if purchase_invoice.is_return else "Purchase"
			}, 'cd'),
			"pmtTyCd": frappe.get_value("RRA Transaction Codes Item", {
				"parent" : "Payment Type",
				"cdnm": purchase_invoice.get('mode_of_payment') or "CASH"
			}, 'cd'),
			"pchsSttsCd": "02" if purchase_invoice.is_return else "05",
			**({"rfdDt": date.strftime("%Y%m%d%H%M%S"), "rfdRsnCd": "03"} if purchase_invoice.is_return else {}),
			"totItemCnt": len(purchase_invoice.items),
			**{ f"taxblAmt{key[0][0]}":
				f"{sum(item.base_net_amount + tax_amounts.get(item.item_code, 0) for item in purchase_invoice.items
					if items.get(item.item_code) == key[0]):.2f}" for key in tax_rates.items()
			},
			**{ f"taxRt{key[0]}": f"{value:.2f}" for key, value in tax_rates.items() },
			**{ f"taxAmt{key[0][0]}": f"{sum(tax_amounts.get(item.item_code, 0) for item in purchase_invoice.items
				if items.get(item.item_code) == key[0]):.2f}" for key in tax_rates.items()
			},
			"totTaxblAmt": f"{purchase_invoice.base_grand_total:.2f}",
			"totTaxAmt": f"{purchase_invoice.base_total_taxes_and_charges:.2f}",
			"totAmt": f"{purchase_invoice.base_grand_total:.2f}",
			"regrNm": shorten_string(purchase_invoice.owner, 60),
			"regrId": shorten_string(purchase_invoice.owner, 20),
			"modrNm": shorten_string(purchase_invoice.modified_by, 60),
			"modrId": shorten_string(purchase_invoice.modified_by, 20),
			"itemList": [
				{
					"itemSeq": item.idx,
					"itemCd": item.item_code,
					"itemClsCd": frappe.get_value("Item", item.item_code, "itemclscd"),
					"itemNm": item.item_name,
					"pkgUnitCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Packing Unit", "cdnm": frappe.get_value("Item", item.item_code, "package_unit") }, 'cd'),
					"qtyUnitCd": frappe.get_value("RRA Transaction Codes Item", { "parent" : "Quantity Unit", "cdnm": item.uom }, 'cd'),
					"qty": int(item.qty),
					"pkg": int(item.qty),
					"prc": f"{item.base_net_rate + (tax_amounts.get(item.item_code, 0) / item.qty):.2f}",
					"splyAmt": f"{item.base_net_amount + tax_amounts.get(item.item_code, 0):.2f}",
					"dcRt": f"{item.discount_percentage:.2f}",
					"dcAmt": f"{item.discount_amount:.2f}",
					"taxTyCd": frappe.get_value("RRA Transaction Codes Item", {"parent" : "Taxation Type", "cdnm": items.get(item.item_code) }, 'cd'),
					"taxblAmt": f"{item.base_net_amount + tax_amounts.get(item.item_code, 0):.2f}",
					"totAmt": f"{item.base_net_amount + tax_amounts.get(item.item_code, 0):.2f}",
					"taxAmt": f"{tax_amounts.get(item.item_code, 0):.2f}",
				} for item in purchase_invoice.items
			]
		})
		log = frappe.get_doc({
			"doctype": "RRA Purchase Invoice Log",
			"purchase_invoice": purchase_invoice_id,
			"invc_no": payload.get("invcNo"),
			"payload": json.dumps(payload),
			"docstatus": 1,
			**({"amended_from": last_log.name} if last_log else {})
		})
		res = self.next(requests.post(url, json=payload), print_if='fail', print_to='frappe')
		if (res.get("resultCd") == "000"):
			log.update({"rra_pushed": 1})
			log.save()
			frappe.msgprint(
				alert=True,
				msg=f"Purchase Invoice successfully submitted to RRA with Invoice No: {log.invc_no}",
				indicator="green"
			)
		elif (res.get("resultCd") == "924"):  # 924 = Duplicate Entry
			log.update({ "error": json.dumps(res), "rra_pushed": 1})
			log.save()
			try:
				self.save_purchase(purchase_invoice_id=purchase_invoice_id)
			except RecursionError:
				frappe.throw("Maximum retries reached while trying to submit purchase invoice to RRA. Please contact support.")
		else:
			log.update({ "error": json.dumps(res) })
			log.save()
			frappe.log_error(message=json.dumps(payload), title="RRA Purchase Submission Failed")
			frappe.msgprint(
				msg="Failed to submit Purchase Invoice to RRA. An hourly retry will be attempted in the background.",
				indicator="red"
			)

	def save_doc(self, doc, ignore_permissions: bool = False):
		"""
			Save document helper method to avoid frappe.db.commit() repetition.
			:param doc: Document to save
			:param ignore_permissions: Ignore permissions while saving
			:return: None
		"""
		doc.save(ignore_permissions=ignore_permissions)
		frappe.db.commit()

	def next(self, response: requests.Response, print_if=None, print_to: str = 'stdout') -> dict:
		if response.ok:
			json_response = response.json()
			if json_response.get("resultCd") == "000":
				if print_if in ['any', 'success']:
					print("RRA Transaction successful:\n", f"{json_response}\n", sep="\n") if print_to == 'stdout' else frappe.msgprint(
						msg=f"RRA Transaction successful:\n{json_response}",
						indicator="green"
					)

				return json_response
			else:
				if print_if in ['any', 'fail']:
					if print_to == 'stdout':
						print("RRA Transaction successful:\n", f"{json_response}\n", sep="\n")
					else:
						frappe.log_error(message=f"RRA Transaction fail:\n{json_response}", title="RRA API Error")
				return { "resultCd": json_response.get("resultCd"), "error": json_response.get("resultMsg") }
		else:
			return {}

	def __str__(self):
		return f"RRAComplianceFactory(base_url={self.BASE_URL}, tin={self.BASE_PAYLOAD['tin']}, bhfId={self.BASE_PAYLOAD['bhfId']})"

	def __repr__(self):
		return self.__str__()


def initialize(action="make", force=False):
	"""  """
	from rra_compliance.utils.customizations import create_dependent_custom_fields, create_independent_custom_fields, delete_all_fields

	rra = RRAComplianceFactory(
		tin=input("Enter init TIN: ").strip(),
		bhf_id=input("Enter Branch ID (default '00'): ").strip() or "00",
		base_url=input("Enter Base URL: ").strip()
	) if action != "destroy" else RRAComplianceFactory()

	if action == "make":
		create_independent_custom_fields()
		print("\n\033[92mSUCCESS \033[0m" + "Custom fields created successfully.\n")
		rra.initialize(action=action)
		rra.get_codes(action=action)

	print(f"Initialized {rra}")

	if action == "make":
		create_dependent_custom_fields()

	update_amendment_settings(action=action)
	if force or input("Run post init methods? (y/n): ").strip().lower() == 'y':
		rra.run_after_init(action=action)
		print("\033[92mSUCCESS \033[0m" + f"{action.capitalize()} action completed.\n")

	if action == "destroy":
		delete_all_fields()
		print("\033[92mSUCCESS \033[0m" + "Custom fields deleted successfully.\n")


def destroy():
	if input("Are you sure you want to destroy all configurations? This action cannot be undone. (y/n): ").strip().lower() == 'y':
		initialize(action="destroy")
	else:
		print("Destroy action cancelled. Database left intact.")


if __name__ == "__main__":
	initialize()

