# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
from webnotes.model.doc import addchild
from webnotes.utils import flt, cstr
import webnotes

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def on_update(self):
		#webnotes.errprint("hello")
		#webnotes.errprint("hiii")
		#accessory=webnotes.conn.sql("select b.item_code from `tabInternal Order Form` a,`tabInternal Order Item Details`b where a.name='IOF-00002'",as_list=1,debug=1)
		#webnotes.errprint(accessory)
		prod=webnotes.conn.sql("select item_code from `tabInternal Order Accessories Details` where item_code is not null and parent='"+self.doc.name+"'")		
		#webnotes.conn.sql("update `tabInternal Order Form` set ascr='"+cstr(prod[0][0])+"' where name='"+self.doc.name+"'",debug=1)
		accessory=webnotes.conn.sql("select item_code from `tabInternal Order Item Details` where item_code is not null and parent='"+self.doc.name+"'")
		bb=''
		#webnotes.errprint(accessory)
		aa=cstr(accessory).replace('(','').replace(')','').replace('u\'','').replace('\'','').replace(',,','<br>')
		#webnotes.errprint(aa) 			
		webnotes.conn.sql("update `tabInternal Order Form` set acr='"+aa+"' where name='"+self.doc.name+"'",debug=1)


	def get_accessories_details(self,item):
                #webnotes.errprint(item)
                qry=webnotes.conn.sql("select default_warehouse,stock_uom from `tabItem` where name='"+item+"'")
                #webnotes.errprint(qry)
                q=webnotes.conn.sql("select description from `tabItem` where name='"+item+"'")
                #webnotes.errprint(q[0][0])
                #qr=webnotes.conn.sql("select sum(actual_qty) from `tabStock Ledger Entry` where item_code='"+item+"' and warehouse='"+qry[0][0]+"'")
                #webnotes.errprint(qr)
                ch = addchild(self.doc, 'internal_order_item',
                                        'Internal Order Item Details', self.doclist)
                #webnotes.errprint(ch)
                ch.item_code= item
                ch.item_name= item
                ch.description= q[0][0]
                ch.qty= 1.00
                ch.export_rate=0.00
                #ch.reserved_warehouse= qry[0][0]
                ch.stock_uom=qry[0][1]
                #ch.actual_qty=qr[0][0]
                ch.ref_rate=0.00
                ch.save(new=1)
	def get_bank_details(self,person):
    		#webnotes.errprint(person)
    		qry=webnotes.conn.sql("select account_no,account_name,bank_name,ifsc_code,branch_name,account_type,bank_address from `tabReferral Master` where name='"+person+"' ")
    		#webnotes.errprint(qry)
    		ret={
		"account_number":qry[0][0],
		"account_name":qry[0][1],
		"bank_name": qry[0][2],
		"ifsc_code": qry[0][3],
		"branch_name": qry[0][4],
		"account_type": qry[0][5],
		"bank_address": qry[0][6]
		}
		return ret




	def get_cust_addr(self):
		from utilities.transaction_base import get_default_address, get_address_display
		res = webnotes.conn.sql("select customer_name from `tabCustomer` where name = '%s'"%self.doc.customer)
		webnotes.errprint(res)
		address_display = None
		customer_address = get_default_address("customer", self.doc.customer)
		#webnotes.errprint(customer_address)
		if customer_address:
			address_display = get_address_display(customer_address)
		ret = { 
			'customer_name'		: res and res[0][0] or '',
			'address_display' : address_display
			#territory':res[0][1]
			}

		return ret
# @webnotes.whitelist()
# def make_sales_order(source_name, target_doclist=None):
# return _make_sales_order(source_name, target_doclist)
	
# def _make_sales_order(source_name, target_doclist=None, ignore_permissions=False):
# 	from webnotes.model.mapper import get_mapped_doclist
	
# 	customer = _make_customer(source_name, ignore_permissions)
	
# 	def set_missing_values(source, target):
# 		if customer:
# 			target[0].customer = customer.doc.name
# 			target[0].customer_name = customer.doc.customer_name
			
# 		si = webnotes.bean(target)
# 		si.run_method("onload_post_render")
			
# 	doclist = get_mapped_doclist("Internal Order Form", source_name, {
# 			"Internal Order Form": {
# 				"doctype": "Sales Order", 
# 				"validation": {
# 					"docstatus": ["=", 1]
# 				}
# 			}, 
# 			"Quotation Item": {
# 				"doctype": "Sales Order Item", 
# 				"field_map": {
# 					"parent": "prevdoc_docname"
# 				}
# 			}, 
# 			"Sales Taxes and Charges": {
# 				"doctype": "Sales Taxes and Charges",
# 				"add_if_empty": True
# 			}, 
# 			"Sales Team": {
# 				"doctype": "Sales Team",
# 				"add_if_empty": True
# 			}
# 		}, target_doclist, set_missing_values, ignore_permissions=ignore_permissions)
		
# 	# postprocess: fetch shipping address, set missing values
		
# 	return [d.fields for d in doclist]

# def _make_customer(source_name, ignore_permissions=False):
# 	#webnotes.errprint("in customer")
# 	quotation = webnotes.conn.get_value("Quotation", source_name, ["lead", "order_type"])
# 	if quotation and quotation[0]:
# 		lead_name = quotation[0]
# 		customer_name = webnotes.conn.get_value("Customer", {"lead_name": lead_name})
# 		if not customer_name:
# 			from selling.doctype.lead.lead import _make_customer
# 			customer_doclist = _make_customer(lead_name, ignore_permissions=ignore_permissions)
# 			customer = webnotes.bean(customer_doclist)
# 			customer.ignore_permissions = ignore_permissions
# 			if quotation[1] == "Shopping Cart":
# 				customer.doc.customer_group = webnotes.conn.get_value("Shopping Cart Settings", None,
# 					"default_customer_group")
			
# 			try:
# 				customer.insert()
# 				return customer
# 			except NameError, e:
# 				if webnotes.defaults.get_global_default('cust_master_name') == "Customer Name":
# 					customer.run_method("autoname")
# 					customer.doc.name += "-" + lead_name
# 					customer.insert()
# 					return customer
# 				else:
# 					raise e
# 			except webnotes.MandatoryError:
# 				from webnotes.utils import get_url_to_form
# 				webnotes.throw(_("Before proceeding, please create Customer from Lead") + \
# 					(" - %s" % get_url_to_form("Lead", lead_name)))
