# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.model.doc import Document
from webnotes.utils import cstr, cint
class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def on_submit(self):
		emp_no = webnotes.conn.sql("select max(employee_number) +1  from `tabEmployee`")	
		bb = (emp_no[0][0])
		cc = cint(bb)
		dd = cstr(cc)
		if self.doc.status =='Approved':

			d = Document('Employee')
			d.employee_name=self.doc.recruiter_name
			d.employee_number= dd
			d.region='Ho'
			d.salutation=self.doc.r_salutations
			d.gender=self.doc.r_gender
			d.date_of_joining=self.doc.posting_date
			d.date_of_birth=self.doc.birth_date
			d.company='Medsynaptic'
			d.save()
