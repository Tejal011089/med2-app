# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
from webnotes.utils import cstr, cint, flt, comma_or, nowdate,add_months,getdate,add_days
import webnotes
import datetime
import time
import calendar
from webnotes.model.doc import addchild
from webnotes.model.bean import getlist
import json
class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def validate(self):
		self.doi()
		self.emp_loan()
	#	self.validate_to_date()

	def doi(self):
		doi1 = time.strftime("%Y-%m-%d")
		#webnotes.errprint((self.doc.doi_start >= doi1))
		if (self.doc.doi_start >= doi1):
			pass
		else:
			webnotes.msgprint("DOI Start date cannot be previous date")
			raise Exception

	def emp_loan(self):
		e_loan=webnotes.conn.sql("""select doi_closing,employee_id from `tabEmployee Loan` where employee_id='%s' and Status='Approved' and docstatus=1 order by creation DESC limit 1"""%self.doc.employee_id,as_list=1)
		#webnotes.errprint(e_loan[0][1])
		if e_loan:
			if e_loan[0][0] >= time.strftime("%Y-%m-%d") :
				webnotes.msgprint("This Employee already Applied for loan..")
				raise Exception
			else:
				pass
		else:
			pass

	def on_submit(self):
		if self.doc.doi_start >= time.strftime("%Y-%m-%d"):
			self.doc.loan_sanction_date = time.strftime("%Y-%m-%d")
		else :
			webnotes.msgprint("DOI Start date is greater than todays date")
			raise Exception
		self.doc.save()

	def validate_to_date(self):
		#ebnotes.errprint("in validate")
		if getdate(self.doc.loan_sanction_date) < getdate(self.doc.doi_start):
			pass

		else:
			#tdate(self.doc.loan_sanction_date) < getdate(self.doc.doi_start)):
			webnotes.msgprint("Date of installament cannot be less than  loan sanction date")
			raise Exception
	#def get_amount_details(self):
	#	#webnotes.errprint("hhhhhhh")
	#	#webnotes.errprint(["hii",s])
	#	amount=(flt(self.doc.loan_amount)+cint(self.doc.amount_as_intrest))/(cint(self.doc.number_of_installments))
	#	webnotes.errprint(amount)
	#	ret={
	#	"amount_per_month":amount
	#	}
	#	return ret
		
		
	def get_loan_details(self):
		end= self.doc.doi_closing
		list1 = []	
		list2= []
		j=self.doc.number_of_installments
		dt=self.doc.doi_start
		#if (self.doc.request_hr_not_to_deduct!=1) or (self.doc.request_hr_not_to_deduct==1 and self.doc.request_status=='Rejected'):
		#	webnotes.errprint("first")

		for j in range(0,j):
			date=add_months(getdate(dt),1)
			
			if date<=getdate(end):
				list1.append(date)
			dt=date
			self.doclist=self.doc.clear_table(self.doclist,'installment')

		for i in list1:
			
			ch = addchild(self.doc, 'installment', 
					'Loan Installment Details', self.doclist)
			ch.date_of_installment = i
			ch.amount_to_be_paid =self.doc.amount_per_month 
			ch.status='Unpaid'	

	def get_deduction_details(self,args):
		#webnotes.errprint(args)
		arg = json.loads(args)
		#webnotes.errprint(arg.get('maxdate'))
		end1=add_months(getdate(arg.get('maxdate')),1)
		#webnotes.errprint(end1)
		#if request=='1':
		#webnotes.errprint("in if ")
		ch = addchild(self.doc, 'installment', 
			'Loan Installment Details', self.doclist)
		ch.date_of_installment = end1
		ch.amount_to_be_paid =self.doc.amount_per_month 
		ch.status='Unpaid'	



				

		# elif self.doc.request_hr_not_to_deduct==1 and self.doc.request_status=='Approved':
		# 	webnotes.errprint("1,approved")
		# 	end1= self.doc.doi_closing
		# 	end=add_months(getdate(end1),1)

		# 	d=self.doc.number_of_installments+cint(1)
		# 	#webnotes.errprint(d)
		# 	dt1 = add_months(getdate(dt),1)
		# 	for j in range(0,d):
		# 		date=add_months(getdate(dt1),1)
		# 		#webnotes.errprint(date)
		# 		if date<=getdate(end):
		# 			list2.append(date)
		# 		dt1=date
		# 		self.doclist=self.doc.clear_table(self.doclist,'installment')
			
		# 	for k in list2:
		# 		#self.doclist=self.doc.clear_table(self.doclist,'installment')
		# 		ch = addchild(self.doc, 'installment', 
		# 				'Loan Installment Details', self.doclist)
		# 		ch.date_of_installment = k
		# 		ch.amount_to_be_paid =self.doc.amount_per_month 
		# 		ch.status='Unpaid'
				
		# elif self.doc.request_hr_not_to_deduct==1 and self.doc.request_status==None:

		# 	webnotes.msgprint("Please Mention Request Status Approved/Rejected ")

