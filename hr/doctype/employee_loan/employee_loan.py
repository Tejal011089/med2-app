# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
from webnotes.utils import cstr, cint, flt, comma_or, nowdate,add_months,getdate,add_days
import webnotes
import datetime
import calendar
from webnotes.model.doc import addchild
class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	#def validate(self):

	#	self.validate_to_date()

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
		#list1.append(self.doc.doi_start)
		#webnotes.errprint(start)
		#webnotes.errprint(number)
		#webnotes.errprint((cstr(self.doc.doi_start) + datetime.timedelta(12*365/12)).isoformat())
		#self.doc.doi_closing=(self.doc.doi_start + datetime.timedelta(12*365/12)).isformat()
		#webnotes.errprint(self.doc.doi_closing)
		#j=0
		j=self.doc.number_of_installments
		dt=self.doc.doi_start
		for j in range(0,j):
			date=add_months(getdate(dt),1)
			#ebnotes.errprint(["j",date])
		 	#ebnotes.errprint(["hii",end])
			if date<=getdate(end):
				list1.append(date)
			dt=date
			#webnotes.errprint(date)
			#ebnotes.errprint(list1)
			self.doclist=self.doc.clear_table(self.doclist,'installment')

		for i in list1:
			#ebnotes.errprint("in for loop")
			#self.doclist=self.doc.clear_table(self.doclist,'installment')
			ch = addchild(self.doc, 'installment', 
					'Loan Installment Details', self.doclist)
			ch.date_of_installment = i
			ch.amount_to_be_paid =self.doc.amount_per_month 
			ch.status='Unpaid'			
#t2= qt*cint(d.get('qty')) 
				#ch.qty=t2	
