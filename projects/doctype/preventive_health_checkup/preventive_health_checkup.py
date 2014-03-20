# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def get_item(self, item):
		webnotes.errprint("in item")
		qry=webnotes.conn.sql("select description from `tabItem` where name=%s",item,as_list=1)
		qr=webnotes.conn.sql("select default_warehouse from `tabItem` where name=%s",item,as_list=1)
		return{
			'description': qry[0][0],
			'warehouse': qr[0][0]
		}

	def get_employee(self, employee):
		#webnotes.errprint("in details")
		webnotes.errprint(["select employee_name,cell_number from `tabEmployee` where name=%s",employee])
		qry=webnotes.conn.sql("select employee_name,cell_number from `tabEmployee` where name=%s",employee,as_list=1)
		qr=webnotes.conn.sql("select cell_number from `tabEmployee` where name=%s",employee,as_list=1)
		return{
			'employee_name': qry[0][0],
			'employee_contact_no': qr[0][0]
		}