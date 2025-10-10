# from typing import Union
import frappe
import requests

from datetime import datetime
from click import progressbar
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from rra_compliance.utils.rra_frappe_translation import rra_to_frappe
from rra_compliance.utils.customizations import custom_fields


class RRAComplianceFactory:
	def __init__(self, tin=None, bhf_id=None, base_url=None):
		settings = {}
		if not base_url or not tin or not bhf_id:
			settings = frappe.get_doc("RRA Settings")

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
			"push_item": "/items/saveItems",
			"update_item_composition": "/items/saveItemComposition",
			"get_imported_items": "/imports/selectImportItems",
			"update_imported_items": "/imports/updateImportItems",
			"update_sales": "/trnsSales/saveSales",
			"get_purchase_sales": "/trnsPurchase/selectTrnsPurchaseSales",
			"update_purchases": "/trnsPurchase/savePurchases",
			"update_stock": "/stockMaster/saveStockMaster",
			"get_stock_items": "/stock/selectStockItems",
			"update_stock_items": "/saveStockItems/saveStockItems"
		}

		#for method in self.endpoints.keys():
		#	self.build_method(method)

	def run_after_init(self, action="make"):
		methods = ['initialize', 'get_codes','get_item_class', 'get_branches', 'get_items']
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
		response_data = self.next(requests.post(url, json=self.get_payload()), print_it=True).get("data", {}).get("info", {})
		if response_data:
			doc = frappe.get_doc({
				"doctype": "RRA Settings",
				"tin": response_data.get("tin"),
				"taxprnm": response_data.get("taxPrNm"),
				"bsnsactv": response_data.get("bsnsActv"),
				"bhfid": response_data.get("bhfId"),
				"brnchnm": response_data.get("brnchNm"),
				"bhfopendt": response_data.get("bhfOpenDt"),
				"prvncnm": response_data.get("prvncNm"),
				"dstrtnm": response_data.get("dstrtNm"),
				"sctrnm": response_data.get("sctrNm"),
				"locdesc": response_data.get("locDesc"),
				"hqyn": 1 if response_data.get("hqYn") == "Y" else 0,
				"mgrnm": response_data.get("mgrNm"),
				"mgrtelno": response_data.get("mgrTelNo"),
				"mgremail": response_data.get("mgrEmail"),
				"dvcid": response_data.get("dvcId"),
				"sdicid": response_data.get("sdicId"),
				"mrcno": response_data.get("mrcNo"),
				"intrlkey": response_data.get("intrnlKey"),
				"signkey": response_data.get("signKey"),
				"cmckey": response_data.get("cmcKey"),
				"base_url": self.BASE_URL,
			})
			if action == "make":
				existing_doc = frappe.get_doc("RRA Settings")
				for field in response_data.keys():
					setattr(existing_doc, field.lower(), response_data.get(field))

				existing_doc.update({
					"base_url": self.BASE_URL,
					"hqyn": 1 if response_data.get("hqYn") == "Y" else 0,
				})
				existing_doc.save(ignore_permissions=True)
				print(f"\n\033[92mSUCCESS \033[0mRRA Settings updated for TIN: {response_data.get('tin')}.\n")

	def get_codes(self, action="make"):
		""" Get codes from RRA and dump them into respective doctypes """
		url = self.get_url(self.endpoints["get_codes"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("clsList", [])
		if response_data:
			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing transaction codes", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					doc = frappe.get_doc({
						"doctype": "RRA Transaction Codes",
						"cdcls": item.get("cdCls"),
						"cdclsnm": item.get("cdClsNm"),
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
									"cdnm": i.get("cdNm"),
									"cddesc": i.get("cdDesc"),
									"useyn": 1 if i.get("useYn") == "Y" else 0,
									"srtord": i.get("srtOrd"),
									"userdfn1": i.get("userDfn1"),
									"userdfn2": i.get("userDfn2"),
									"userdfn3": i.get("userDfn3"),
								})

							doc.insert(ignore_permissions=True)
							bar.update(1, f"Created Code: {item.get('cdCls')} - {item.get('cdClsNm')}")

					elif action == "destroy":
						doc.delete()
						bar.update(1, f"Deleted Code: {item.get('cdCls')} - {item.get('cdClsNm')}")

			print("\n\033[92mSUCCESS \033[0mCodes synchronization completed.\n")
		else:
			print("No codes found in the response.")

	def get_item_class(self, action="make"):
		""" Get items classes from RRA and dump them into item group """
		url = self.get_url(self.endpoints["get_item_class"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("itemClsList", [])
		if response_data:
			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing item groups", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					doc = frappe.get_doc({
						"doctype": "Item Group",
						"item_group_name": item.get("itemClsNm"),
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

				print("\n\033[92mSUCCESS \033[0mItem Categories synchronization completed.\n")
		else:
			print("No item classes found in the response.")

	def get_customer(self, customer_tin, action="make"):
		""" Get customers from RRA and dump them into customer doctype """
		url = self.get_url(self.endpoints["get_customer"])
		response_data = self.next(requests.post(url, json=self.get_payload(custmTin=customer_tin))).get("data", {}).get("custList", [])
		if response_data:
			item = response_data[0]
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

	def get_branches(self, action="make"):
		""" Get branches from RRA and dump them into branch doctype """
		url = self.get_url(self.endpoints["get_branches"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("bhfList", [])
		if response_data:
			with progressbar(length=len(response_data), empty_char=" ", fill_char="=", label="Syncing branches", show_pos=True, item_show_func=lambda x: x) as bar:
				for item in response_data:
					doc = frappe.get_doc({
						"doctype": "Branch",
						"branch": item.get("brnchNm"),
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

					print("\n\033[92mSUCCESS \033[0mBranches synchronization completed.\n")

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
					doc = frappe.get_doc({
						"doctype": "Item",
						"item_code": item.get("itemCd"),
						"item_name": item.get("itemNm"),
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

			print("\n\033[92mSUCCESS \033[0mItems synchronization completed.\n")
		else:
			print("No items found in the response.")

	def push_item(self, item_code: str):
		"""
			Push item to RRA.
		"""
		url = self.get_url(self.endpoints['create_items'])
		doc = frappe.get_doc("Item", item_code)
		payload = self.get_payload(**{
			"itemCd": doc.get('item_code'),
			"itemClsCd": doc.get('itemclscd'),
			"itemNm": doc.get('item_name'),
			"pkgUnitCd": 'NT',  # doc.packaging_unit, # Simplifying my life here but can be done properly later
			"itemTyCd": frappe.get_doc({ "doctype": "RRA Transaction Codes Item", "parent" : "Item Type", "cdnm": doc.get('item_type') }).get('cd'),
			"orgnNatCd": frappe.get_doc({ "doctype": "RRA Transaction Codes Item", "parent" : "Cuntry", "cdnm": doc.get('origin_country') }).get('cd'),
			"qtyUnitCd": frappe.get_doc({ "doctype": "RRA Transaction Codes Item", "parent" : "Quantity Unit", "cdnm": doc.get('quantity_unit') }).get('cd'),
			"taxTyCd": frappe.get_doc({ "doctype": "RRA Transaction Codes Item", "parent" : "Taxation Type", "cdnm": doc.get('tax_type') }).get('cd'),
			"isrcAplcbYn": "Y" if doc.get('isrc_applicable') else "N",
			"useYn": "N" if doc.get('disabled') else "Y",
			"regrNm": "Admin",
			"regrId": "Admin",
			"modrNm": "Admin",
			"modrId": "Admin"
		})
		response = self.next(requests.post(url, json=payload))
		if response.get("resultCd") == "000":
			doc.rra_pushed = 1
			doc.save(ignore_permissions=True)
			frappe.msgprint(
				msg=f"Item {doc.get('item_code')} pushed to RRA successfully.",
				indicator="green"
			)

		else:
			frappe.msgprint(
				msg=f"Failed to push item {doc.get('item_code')} to RRA. An hourly retry will be attempted in the background.",
				indicator="red"
			)
			frappe.enqueue(self.push_item, item_code=item_code, queue='long', timeout=1500)

	def build_method(self, method):
		"""
			Dynamically build methods for each endpoint.
			This will be reimplemented later.
		"""
		if not hasattr(self, method):
			def api_method(**kwargs):
				url = self.get_url(self.endpoints[method])
				payload = self.get_payload(**kwargs)
				response = requests.post(url, json=payload)
				self.next(response, print_it=kwargs.get("print") or False)

			self.__setattr__(method, api_method)

	def next(self, response: requests.Response, print_it: bool = False) -> dict:
		if response.ok and response.json().get("resultCd") == "000":
			if print_it:
				print("API call successful:\n", f"{response.json()}\n", sep="\n")

			return response.json()
		else:
			return {}

	def __str__(self):
		return f"RRAComplianceFactory(base_url={self.BASE_URL}, tin={self.BASE_PAYLOAD['tin']}, bhf_id={self.BASE_PAYLOAD['bhf_id']})"

	def __repr__(self):
		return self.__str__()


def create_fields():
	create_custom_fields(custom_fields)
	print("\n\033[92mSUCCESS \033[0m" + "Custom fields created successfully.\n")


def delete_fields():
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			"Custom Field",
			{
				"fieldname": ("in", [field["fieldname"] for field in fields]),
				"dt": doctype,
			},
		)

		frappe.clear_cache(doctype=doctype)

	print("\033[92mSUCCESS \033[0m" + "Custom fields deleted successfully.\n")


def initialize(action="make", force=False):
	"""  """
	rra = RRAComplianceFactory(
		tin=input("Enter init TIN: ").strip(),
		bhf_id=input("Enter Branch ID (default '00'): ").strip() or "00",
		base_url=input("Enter Base URL: ").strip()
	) if action != "destroy" else RRAComplianceFactory()

	print(f"Initialized {rra}")

	if action == "make":
		create_fields()

	if force or input("Run initial data fetch? (y/n): ").strip().lower() == 'y':
		rra.run_after_init(action=action)
		print("\033[92mSUCCESS \033[0m" + f"{action.capitalize()} action completed.\n")

	if action == "destroy":
		delete_fields()


def destroy():
	if input("Are you sure you want to destroy all configurations? This action cannot be undone. (y/n): ").strip().lower() == 'y':
		initialize(action="destroy")
	else:
		print("Destroy action cancelled. Database left intact.")


if __name__ == "__main__":
	initialize()

