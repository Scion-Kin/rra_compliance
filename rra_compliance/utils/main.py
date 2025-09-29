# from datetime import datetime
# from typing import Union

import frappe
# import json
import os
import requests


class RRAComplianceFactory:
	BASE_URL = ""
	BASE_PAYLOAD = {}

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

		for method in self.endpoints.keys():
			self.build_method(method)

	def run_after_init(self):
		self.get_item_class()

	def get_url(self, endpoint):
		return f"{self.BASE_URL}{endpoint}"

	def get_payload(self, **kwargs):
		payload = self.BASE_PAYLOAD.copy()
		payload.update(kwargs)
		return payload

	def get_item_class(self):
		""" Get items classes from RRA and dump them into item group """
		url = self.get_url(self.endpoints["get_item_class"])
		response_data = self.next(requests.post(url, json=self.get_payload(lastReqDt="20180520000000"))).get("itemClassList", [])
		if response_data:
			for item in response_data:
				if not frappe.db.exists("Item Group", item.get("itemClsNm")):
					doc = frappe.get_doc({
						"doctype": "Item Group",
						"item_group_name": item.get("itemClsNm"),
						"item_group_code": item.get("itemClsCd")
					})
					doc.insert(ignore_permissions=True)
					print(f"Created Item Category: {item.get('itemClsCd')} - {item.get('itemClsNm')}")
				else:
					print(f"Item Category already exists: {item.get('itemClsCd')} - {item.get('itemClsNm')}")
		else:
			print("No item classes found in the response.")

	def build_method(self, method):
		""""""
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


rra = None
def initialize():
	"""  """
	tin = os.getenv('rra_tin') or input("Enter TIN: ").strip()
	bhf_id = os.getenv('rra_bhf_id') or input("Enter Branch ID (default '00'): ").strip() or "00"
	base_url = os.getenv('rra_base_url') or input("Enter Base URL: ").strip()
	rra = RRAComplianceFactory(tin=tin, bhf_id=bhf_id, base_url=base_url)
	print(f"Initialized RRAComplianceFactory with TIN: {tin}, Branch ID: {bhf_id}, Base URL: {base_url}")

	if input("Run initial data fetch? (y/n): ").strip().lower() == 'y':
		rra.run_after_init()


if __name__ == "__main__":
	# import argparse
	# parser = argparse.ArgumentParser(description="RRA Compliance Utility")
	# parser.add_argument("--action", choices=[i for i in rra.endpoints.keys() if i], required=True, help="Action to perform")
	# parser.add_argument("--payload", type=str, help="JSON payload for the API call")
	# args = parser.parse_args()
	initialize()

	# action = args.action
	# if action in rra.endpoints:
	# 	getattr(rra, action)(**(json.loads(args.payload) if args.payload else {}))
	# else:
	# 	print(f"Invalid action: {action}")
