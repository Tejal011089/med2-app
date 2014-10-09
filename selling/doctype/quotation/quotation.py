# # Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# # License: GNU General Public License v3. See license.txt

# from __future__ import unicode_literals
# import webnotes

# from webnotes.utils import cstr
# from webnotes.model.bean import getlist
# from webnotes.model.code import get_obj
# from webnotes import _, msgprint

# sql = webnotes.conn.sql
	

# from controllers.selling_controller import SellingController

# class DocType(SellingController):
# 	def __init__(self, doc, doclist=[]):
# 		self.doc = doc
# 		self.doclist = doclist
# 		self.tname = 'Quotation Item'
# 		self.fname = 'quotation_details'
		 
# 	# Get contact person details based on customer selected
# 	# ------------------------------------------------------
# 	def get_contact_details(self):
# 		return get_obj('Sales Common').get_contact_details(self,0)
	
# 	# Get Item Details
# 	# -----------------
# 	def get_item_details(self, args=None):
# 		import json
# 		args = args and json.loads(args) or {}
# 		if args.get('item_code'):
# 			return get_obj('Sales Common').get_item_details(args, self)
# 		else:
# 			obj = get_obj('Sales Common')
# 			for doc in self.doclist:
# 				if doc.fields.get('item_code'):
# 					arg = {
# 						'item_code': doc.fields.get('item_code'),
# 						'income_account': doc.fields.get('income_account'),
# 						'cost_center': doc.fields.get('cost_center'),
# 						'warehouse': doc.fields.get('warehouse')
# 					}
# 					res = obj.get_item_details(arg, self) or {}
# 					for r in res:
# 						if not doc.fields.get(r):
# 							doc.fields[r] = res[r]

# 	# Re-calculates Basic Rate & amount based on Price List Selected
# 	# --------------------------------------------------------------
# 	def get_adj_percent(self, arg=''):
# 		get_obj('Sales Common').get_adj_percent(self)
	
		
# 	# Get Tax rate if account type is TAX
# 	# -----------------------------------
# 	def get_rate(self,arg):
# 		return get_obj('Sales Common').get_rate(arg)
	
# 	# Does not allow same item code to be entered twice
# 	# -------------------------------------------------
# 	def validate_for_items(self):
# 		chk_dupl_itm = []
# 		for d in getlist(self.doclist,'quotation_details'):
# 			if [cstr(d.item_code),cstr(d.description)] in chk_dupl_itm:
# 				msgprint("Item %s has been entered twice. Please change description atleast to continue" % d.item_code)
# 				raise Exception
# 			else:
# 				chk_dupl_itm.append([cstr(d.item_code),cstr(d.description)])


# 	#do not allow sales item in maintenance quotation and service item in sales quotation
# 	#-----------------------------------------------------------------------------------------------
# 	def validate_order_type(self):
# 		super(DocType, self).validate_order_type()
		
# 		if self.doc.order_type in ['Maintenance', 'Service']:
# 			for d in getlist(self.doclist, 'quotation_details'):
# 				is_service_item = sql("select is_service_item from `tabItem` where name=%s", d.item_code)
# 				is_service_item = is_service_item and is_service_item[0][0] or 'No'
				
# 				if is_service_item == 'No':
# 					msgprint("You can not select non service item "+d.item_code+" in Maintenance Quotation")
# 					raise Exception
# 		else:
# 			for d in getlist(self.doclist, 'quotation_details'):
# 				aa="select is_sales_item from `tabItem` where name='"+d.item_code+"'"
# 				# webnotes.errprint(aa)
# 				is_sales_item = webnotes.conn.sql(aa)
# 				# webnotes.errprint(is_sales_item)
# 				is_sales_item = is_sales_item and is_sales_item[0][0] or 'No'
# 				webnotes.errprint(is_sales_item)
# 				if is_sales_item == 'No':
# 					msgprint("You can not select non sales item "+d.item_code+" in Sales Quotation")
# 					raise Exception
	
# 	def validate(self):
# 		super(DocType, self).validate()
		
# 		import utilities
# 		if not self.doc.status:
# 			self.doc.status = "Draft"
# 		else:
# 			utilities.validate_status(self.doc.status, ["Draft", "Submitted", 
# 				"Order Confirmed", "Order Lost", "Cancelled"])

# 		self.validate_order_type()
# 		self.validate_for_items()

# 		self.validate_uom_is_integer("stock_uom", "qty")

# 		sales_com_obj = get_obj('Sales Common')
# 		#sales_com_obj.check_active_sales_items(self)
# 		#sales_com_obj.validate_max_discount(self,'quotation_details')

# 	def on_update(self):
# 		# Set Quotation Status
# 		webnotes.conn.set(self.doc, 'status', 'Draft')
	
# 	#update enquiry
# 	#------------------
# 	def update_enquiry(self, flag):
# 		prevdoc=''
# 		for d in getlist(self.doclist, 'quotation_details'):
# 			if d.prevdoc_docname:
# 				prevdoc = d.prevdoc_docname
		
# 		if prevdoc:
# 			if flag == 'submit': #on submit
# 				sql("update `tabOpportunity` set status = 'Quotation Sent' where name = %s", prevdoc)
# 			elif flag == 'cancel': #on cancel
# 				sql("update `tabOpportunity` set status = 'Open' where name = %s", prevdoc)
# 			elif flag == 'order lost': #order lost
# 				sql("update `tabOpportunity` set status = 'Opportunity Lost' where name=%s", prevdoc)
# 			elif flag == 'order confirm': #order confirm
# 				sql("update `tabOpportunity` set status='Order Confirmed' where name=%s", prevdoc)
	
# 	# declare as order lost
# 	#-------------------------
# 	def declare_order_lost(self, arg):
# 		chk = sql("select t1.name from `tabSales Order` t1, `tabSales Order Item` t2 where t2.parent = t1.name and t1.docstatus=1 and t2.prevdoc_docname = %s",self.doc.name)
# 		if chk:
# 			msgprint("Sales Order No. "+cstr(chk[0][0])+" is submitted against this Quotation. Thus 'Order Lost' can not be declared against it.")
# 			raise Exception
# 		else:
# 			webnotes.conn.set(self.doc, 'status', 'Order Lost')
# 			webnotes.conn.set(self.doc, 'order_lost_reason', arg)
# 			self.update_enquiry('order lost')
# 			return 'true'
	
# 	#check if value entered in item table
# 	#--------------------------------------
# 	def check_item_table(self):
# 		if not getlist(self.doclist, 'quotation_details'):
# 			msgprint("Please enter item details")
# 			raise Exception
		
# 	# ON SUBMIT
# 	# =========================================================================
# 	def on_submit(self):
# 		self.check_item_table()
		
# 		# Check for Approving Authority
# 		get_obj('Authorization Control').validate_approving_authority(self.doc.doctype, self.doc.company, self.doc.grand_total, self)

# 		# Set Quotation Status
# 		webnotes.conn.set(self.doc, 'status', 'Submitted')
		
# 		#update enquiry status
# 		self.update_enquiry('submit')
		
		
# # ON CANCEL
# # ==========================================================================
# 	def on_cancel(self):
# 		#update enquiry status
# 		self.update_enquiry('cancel')
		
# 		webnotes.conn.set(self.doc,'status','Cancelled')
			
# # Print other charges
# # ===========================================================================
# 	def print_other_charges(self,docname):
# 		print_lst = []
# 		for d in getlist(self.doclist,'other_charges'):
# 			lst1 = []
# 			lst1.append(d.description)
# 			lst1.append(d.total)
# 			print_lst.append(lst1)
# 		return print_lst

# @webnotes.whitelist()
# def make_internal_order(source_name, target_doclist=None):
# 	#webnotes.errprint("in internal order")	
# 	return _make_internal_order(source_name, target_doclist)

# def _make_internal_order(source_name, target_doclist=None, ignore_permissions=False):
# 	#webnotes.errprint("in make internal order 2")
# 	from webnotes.model.mapper import get_mapped_doclist

# 	customer = _make_customer(source_name, ignore_permissions)

# 	def set_missing_values(source, target):
# 		if customer:
# 			target[0].customer = customer.doc.name
# 			target[0].customer_name = customer.doc.customer_name
			
# 		si = webnotes.bean(target)
# 		si.run_method("onload_post_render")
			
# 	doclist = get_mapped_doclist("Quotation", source_name, {
# 			"Quotation": {
# 				"doctype": "Internal Order Form", 
# 				"validation": {
# 					"docstatus": ["=", 1]
# 				}
# 			}, 
# 			"Quotation Item": {
# 				"doctype": "Quotation Item", 
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




# # @webnotes.whitelist()
# # def make_sales_order(source_name, target_doclist=None):
# # 	return _make_sales_order(source_name, target_doclist)
	
# # def _make_sales_order(source_name, target_doclist=None, ignore_permissions=False):
# # 	from webnotes.model.mapper import get_mapped_doclist
	
# # 	customer = _make_customer(source_name, ignore_permissions)
	
# # 	def set_missing_values(source, target):
# # 		if customer:
# # 			target[0].customer = customer.doc.name
# # 			target[0].customer_name = customer.doc.customer_name
			
# # 		si =t

from __future__ import unicode_literals
import webnotes

from webnotes.utils import cstr
from webnotes.model.bean import getlist
from webnotes.model.code import get_obj
from webnotes import _, msgprint
from webnotes.model.doc import addchild

	

from controllers.selling_controller import SellingController

class DocType(SellingController):
	def __init__(self, doc, doclist=[]):
		self.doc = doc
		self.doclist = doclist
		self.tname = 'Quotation Item'
		self.fname = 'quotation_details'

	def has_sales_order(self):
		return webnotes.conn.get_value("Sales Order Item", {"prevdoc_docname": self.doc.name, "docstatus": 1})

	def validate_for_items(self):
		chk_dupl_itm = []
		for d in getlist(self.doclist,'quotation_details'):
			if [cstr(d.item_code),cstr(d.description)] in chk_dupl_itm:
				msgprint("Item %s has been entered twice. Please change description atleast to continue" % d.item_code)
				raise Exception
			else:
				chk_dupl_itm.append([cstr(d.item_code),cstr(d.description)])

	def validate_order_type(self):
		super(DocType, self).validate_order_type()
		
		if self.doc.order_type in ['Maintenance', 'Service']:
			for d in getlist(self.doclist, 'quotation_details'):
				is_service_item = webnotes.conn.sql("select is_service_item from `tabItem` where name=%s", d.item_code)
				is_service_item = is_service_item and is_service_item[0][0] or 'No'
				
				if is_service_item == 'No':
					msgprint("You can not select non service item "+d.item_code+" in Maintenance Quotation")
					raise Exception
		else:
			for d in getlist(self.doclist, 'quotation_details'):
				is_sales_item = webnotes.conn.sql("select is_sales_item from `tabItem` where name=%s", d.item_code)
				is_sales_item = is_sales_item and is_sales_item[0][0] or 'No'
				
				if is_sales_item == 'No':
					msgprint("You can not select non sales item "+d.item_code+" in Sales Quotation")
					raise Exception
	
	def validate(self):
		super(DocType, self).validate()
		self.set_status()
		self.validate_order_type()
		self.validate_for_items()
		self.validate_uom_is_integer("stock_uom", "qty")


	def get_accessories_details(self,item):
                qry=webnotes.conn.sql("select default_warehouse,stock_uom from `tabItem` where name='"+item+"'")
                q=webnotes.conn.sql("select description from `tabItem` where name='"+item+"'")
                qr=webnotes.conn.sql("select sum(actual_qty) from `tabStock Ledger Entry` where item_code='"+item+"' and warehouse='"+qry[0][0]+"'")
                ch = addchild(self.doc, 'quotation_details','Quotation Item', self.doclist)
                ch.item_code= item
                ch.item_name= item
                ch.description= q[0][0]
                ch.qty= 1.00
                ch.export_rate=0.00
                ch.stock_uom=qry[0][1]
                ch.adj_rate=0.00
                ch.save(new=1)

	def update_opportunity(self):
		for opportunity in self.doclist.get_distinct_values("prevdoc_docname"):
			webnotes.bean("Opportunity", opportunity).get_controller().set_status(update=True)
	
	def declare_order_lost(self, arg):
		if not self.has_sales_order():
			webnotes.conn.set(self.doc, 'status', 'Lost')
			webnotes.conn.set(self.doc, 'order_lost_reason', arg)
			self.update_opportunity()
		else:
			webnotes.throw(_("Cannot set as Lost as Sales Order is made."))
	
	def check_item_table(self):
		if not getlist(self.doclist, 'quotation_details'):
			msgprint("Please enter item details")
			raise Exception
		
	def on_submit(self):
		self.check_item_table()
		
		# Check for Approving Authority
		get_obj('Authorization Control').validate_approving_authority(self.doc.doctype, self.doc.company, self.doc.grand_total, self)
			
		#update enquiry status
		self.update_opportunity()
		
	def on_cancel(self):
		#update enquiry status
		self.set_status()
		self.update_opportunity()
			
	def print_other_charges(self,docname):
		print_lst = []
		for d in getlist(self.doclist,'other_charges'):
			lst1 = []
			lst1.append(d.description)
			lst1.append(d.total)
			print_lst.append(lst1)
		return print_lst


	# def get_accessories(self,item_code):
	# 	webnotes.errprint("get_accessories")
	# 	webnotes.errprint(item_code)
	# 	accessories= webnotes.conn.sql(""" select item_code from `tabAccessories` 
	# 		      where parent='%s'"""%item_code,debug=1)
	# 	webnotes.errprint(accessories)
	# 	if accessories:
	# 		for i in accessories:
	# 			webnotes.errprint(i)
	# 			ch = addchild(self.doc, 'accessories_details',
 #    				'Accessories', self.doclist)
	# 			ch.itemcode=i
				
		
	
@webnotes.whitelist()
def make_sales_order(source_name, target_doclist=None):
	return _make_sales_order(source_name, target_doclist)
	
def _make_sales_order(source_name, target_doclist=None, ignore_permissions=False):
	from webnotes.model.mapper import get_mapped_doclist
	
	customer = _make_customer(source_name, ignore_permissions)
	
	def set_missing_values(source, target):
		if customer:
			target[0].customer = customer.doc.name
			target[0].customer_name = customer.doc.customer_name
			
		si = webnotes.bean(target)
		si.run_method("onload_post_render")
			
	doclist = get_mapped_doclist("Quotation", source_name, {
			"Quotation": {
				"doctype": "Sales Order", 
				"validation": {
					"docstatus": ["=", 1]
				}
			}, 
			"Accessories Details": {
				"doctype": "Accessories Details", 
				"field_map": {
					"parent": "prevdoc_docname"
				}
			},
			"Quotation Item": {
				"doctype": "Sales Order Item", 
				"field_map": {
					"parent": "prevdoc_docname"
				}
			}, 
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"add_if_empty": True
			}, 
			"Sales Team": {
				"doctype": "Sales Team",
				"add_if_empty": True
			}
		}, target_doclist, set_missing_values, ignore_permissions=ignore_permissions)
		
	# postprocess: fetch shipping address, set missing values
		
	return [d.fields for d in doclist]

def get_tax(doctype, txt, searchfield, start, page_len, filters):
		webnotes.errprint("pincode")
		return webnotes.conn.sql("""select parent from `tabApplicable Territory` 
		where territory=%s 
		or territory='All Territories'"""%self.doc.territory)
		

# @webnotes.whitelist()
# def make_internal_order(source_name, target_doclist=None):
# 	#webnotes.errprint("in internal order")	
# 	return _make_internal_order(source_name, target_doclist)

# def _make_internal_order(source_name, target_doclist=None, ignore_permissions=False):
# 	#webnotes.errprint("in make internal order 2")
# 	from webnotes.model.mapper import get_mapped_doclist

# 	customer = _make_customer(source_name, ignore_permissions)

# 	def set_missing_values(source, target):
# 		if customer:
# 			target[0].customer = customer.doc.name
# 			target[0].customer_name = customer.doc.customer_name
			
# 		si = webnotes.bean(target)
# 		si.run_method("onload_post_render")
			
# 	doclist = get_mapped_doclist("Quotation", source_name, {
# 			"Quotation": {
# 				"doctype": "Internal Order Form", 
# 				"validation": {
# 					"docstatus": ["=", 1]
# 				}
# 			}, 
# 			"Quotation Item": {
# 				"doctype": "Quotation Item", 
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

def _make_customer(source_name, ignore_permissions=False):
	quotation = webnotes.conn.get_value("Quotation", source_name, ["lead", "order_type"])
	if quotation and quotation[0]:
		lead_name = quotation[0]
		customer_name = webnotes.conn.get_value("Customer", {"lead_name": lead_name})
		if not customer_name:
			from selling.doctype.lead.lead import _make_customer
			customer_doclist = _make_customer(lead_name, ignore_permissions=ignore_permissions)
			customer = webnotes.bean(customer_doclist)
			customer.ignore_permissions = ignore_permissions
			if quotation[1] == "Shopping Cart":
				customer.doc.customer_group = webnotes.conn.get_value("Shopping Cart Settings", None,
					"default_customer_group")
			
			try:
				customer.insert()
				return customer
			except NameError, e:
				if webnotes.defaults.get_global_default('cust_master_name') == "Customer Name":
					customer.run_method("autoname")
					customer.doc.name += "-" + lead_name
					customer.insert()
					return customer
				else:
					raise
			except webnotes.MandatoryError:
				from webnotes.utils import get_url_to_form
				webnotes.throw(_("Before proceeding, please create Customer from Lead") + \
					(" - %s" % get_url_to_form("Lead", lead_name)))
