# from datetime import datetime
# from typing import Union

import frappe
import os
import requests
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from rra_compliance.utils.rra_frappe_translation import rra_to_frappe
from rra_compliance.utils.customizations import custom_fields


class RRAComplianceFactory:
	def __init__(self, tin, bhf_id="00", base_url=None):
		if not base_url or not isinstance(base_url, str):
			raise ValueError("Base URL must be a valid string.")
		if not tin or not isinstance(tin, str):
			raise ValueError("TIN must be a valid string.")
		if not bhf_id or not isinstance(bhf_id, str):
			raise ValueError("Branch ID must be a valid string.")

		self.BASE_URL = base_url
		self.BASE_PAYLOAD = {"tin": tin, "bhfId": bhf_id}
		self.endpoints = {
			"initialize": "/initializer/selectInitInfo",
			"get_codes": "/code/selectCodes",
			"get_item_class": "/itemClass/selectItemsClass",
			"get_customers": "/customers/selectCustomer",
			"get_branches": "/branches/selectBranches",
			"get_notices": "/notices/selectNotices",
			"update_branch_customers": "/branches/saveBrancheCustomers",
			"update_branch_users": "/branches/saveBrancheUsers",
			"update_branch_insurances": "/branches/saveBrancheInsurances",
			"get_items": "/items/selectItems",
			"create_items": "/items/saveItems",
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
		methods = [ i for i in self.endpoints.keys() if getattr(self, i, None) ]
		for method in methods:
			print(f"Running method: {method}()")
			getattr(self, method)(action=action)

	def get_url(self, endpoint):
		return f"{self.BASE_URL}{endpoint}"

	def get_payload(self, **kwargs):
		payload = self.BASE_PAYLOAD.copy()
		payload.update(kwargs)
		return payload

	def get_codes(self, action="make"):
		""" Get codes from RRA and dump them into respective doctypes """
		url = self.get_url(self.endpoints["get_codes"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("clsList", [])
		if response_data:
			for item in response_data:
				doc = frappe.get_doc({
					"doctype": "RRA Transaction Codes",
					"cdcls": item.get("cdCls"),
					"cdclsnm": item.get("cdClsNm"), # Auto frappe doc name
					"cdclsdesc": item.get("cdClsDesc"),
					"useyn": 1 if item.get("useYn") == "Y" else 0,
					"relation": rra_to_frappe.get(item.get("cdClsNm")),
					"userdfnnm1": item.get("userDfnNm1"),
					"userdfnnm2": item.get("userDfnNm2"),
					"userdfnnm3": item.get("userDfnNm3"),
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
						print(f"Created Code: {item.get('cdCls')} - {item.get('cdClsNm')}")
					else:
						print(f"Code already exists: {item.get('cdCls')} - {item.get('cdClsNm')}")

				elif action == "destroy":
					doc.delete()
					print(f"Deleted Code: {item.get('cdCls')} - {item.get('cdClsNm')}")

			print("\n\033[92mSUCCESS \033[0m" + "Codes synchronization completed.\n")
		else:
			print("No codes found in the response.")

	def get_item_class(self, action="make"):
		""" Get items classes from RRA and dump them into item group """
		url = self.get_url(self.endpoints["get_item_class"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("data", {}).get("itemClsList", [])
		if response_data:
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
						print(f"Created Item Category: {item.get('itemClsCd')} - {item.get('itemClsNm')}")
					else:
						print(f"Item Category already exists: {item.get('itemClsCd')} - {item.get('itemClsNm')}")

				elif action == "destroy":
					doc.delete()
					print(f"Deleted Item Category: {item.get('itemClsCd')} - {item.get('itemClsNm')}")

			print("\n\033[92mSUCCESS \033[0m" + "Item Categories synchronization completed.\n")
		else:
			print("No item classes found in the response.")

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

	print("\n\033[92mSUCCESS \033[0m" + "Custom fields deleted successfully.\n")


def initialize(action="make", force=False):
	"""  """
	tin = os.getenv('rra_tin') or input("Enter TIN: ").strip()
	bhf_id = os.getenv('rra_bhf_id') or input("Enter Branch ID (default '00'): ").strip() or "00"
	base_url = os.getenv('rra_base_url') or input("Enter Base URL: ").strip()
	rra = RRAComplianceFactory(tin=tin, bhf_id=bhf_id, base_url=base_url)
	print(f"Initialized RRAComplianceFactory with TIN: {tin}, Branch ID: {bhf_id}, Base URL: {base_url}")

	if action == "make":
		create_fields()

	if force or input("Run initial data fetch? (y/n): ").strip().lower() == 'y':
		rra.run_after_init(action=action)
		print("\n\033[92mSUCCESS \033[0m" + f"{action.capitalize()} action completed.\n")

	if action == "destroy":
		delete_fields()


def destroy():
	if input("Are you sure you want to destroy all configurations? This action cannot be undone. (y/n): ").strip().lower() == 'y':
		initialize(action="destroy")
	else:
		print("Destroy action cancelled. Database left intact.")


if __name__ == "__main__":
	initialize()

