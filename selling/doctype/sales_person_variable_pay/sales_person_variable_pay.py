# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.utils import add_days, cint, cstr, flt, getdate, nowdate, _round,now
import datetime
import dateutil.relativedelta
from webnotes.model.doc import Document

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl
		self.quater_month=3
		self.prev_month=1
		self.months={1:'January-March',4:'April-June',7:'July-September',10:'October-December'}
		self.fiscal_year=webnotes.conn.sql("select name from `tabFiscal Year` where year_start_date<='%s' and '%s' <= year_end_date"%(self.from_date(self.quater_month).strftime('%Y-%m-%d'),self.to_date().strftime('%Y-%m-%d')),as_list=1)

	def on_update(self):
		self.update_sales_person_eligibility()
		self.update_jv()

	def update_sales_person_eligibility(self):
		sales_persons=webnotes.conn.sql('select distinct sales_person from `tabSales Team`',as_list=1)
		for person in sales_persons:
			person_allocated_amt=self.calculate_allocated_amt(person[0])
			if person_allocated_amt[0][0]!=0:
				eligibility=self.check_eligible(person[0],person_allocated_amt[0][0])

	def check_eligible(self,person,person_allocated_amt):
		if self.fiscal_year:
			target_amt_percent=self.target_all_details(person,(self.fiscal_year)[0][0],self.months.get(cint(self.from_date(self.quater_month).month)))
			if target_amt_percent:
				for amt in target_amt_percent:
					quater_target_amount=flt(amt[0])*flt(amt[1])/flt(100)
					percent=flt(person_allocated_amt)/flt(quater_target_amount)*100
					if percent >= 75:
						webnotes.conn.sql("""update `tabSales Team` set eligible='True',fiscal_year='%s',quater='%s' where sales_person='%s' 
							and parent in (select name from `tabSales Order` where transaction_date between '%s' and '%s') and docstatus=1"""%((self.fiscal_year)[0][0],self.months.get(cint(self.from_date(self.quater_month).month)),person,self.from_date(self.quater_month),self.to_date()))
						webnotes.conn.sql("commit")

	def calculate_allocated_amt(self,person):
		return webnotes.conn.sql("""select ifnull(sum(st.allocated_amount),0) from 
				`tabSales Team` as st,`tabSales Order` as so 
				where st.parent=so.name and so.docstatus=1 and st.parenttype='Sales Order' and st.sales_person='%s' and 
				so.transaction_date between '%s' and '%s'"""%(person,self.from_date(self.quater_month).strftime('%Y-%m-%d %H:%M:%S'),self.to_date().strftime('%Y-%m-%d %H:%M:%S')),as_list=1)

	def target_all_details(self,person,fiscal_year,quater_month):
		if fiscal_year:
			return webnotes.conn.sql("""SELECT td.target_amount,bdt.percentage_allocation,td.variable_pay
			 FROM `tabTarget Detail` AS td,`tabBudget Distribution Detail` AS bdt,`tabSales Person` AS sp 
			 WHERE td.parent=sp.name and sp.distribution_id=bdt.parent and td.fiscal_year='%(year)s' 
			 and bdt.month='%(month)s' and sp.name='%(person)s'"""%{'year':fiscal_year,'month':quater_month,'person':person},as_list=1)

	def to_date(self):
		return datetime.datetime.now() - dateutil.relativedelta.relativedelta(days=1)

	def from_date(self,month):
		return datetime.datetime.now() - dateutil.relativedelta.relativedelta(months=cint(month))

	def update_jv(self):
		jv_details=webnotes.conn.sql("select name,sales_order_number,total_debit from `tabJournal Voucher` where docstatus=1 and ifnull(sales_order_number,'')<>'' and status='False'",as_list=1)
		if jv_details:
			for jv in jv_details:
				so_details=webnotes.conn.sql(""" select sales_person,allocated_percentage,quater,fiscal_year from `tabSales Team`
					where parent='%s' and ifnull(quater,'')<>'' and eligible='True' and ifnull(fiscal_year,'')<>''"""%(jv[1]),as_list=1)
				if so_details:
					for so in so_details:
						jvp=Document('Variable Pay Summary')
						jvp.sales_person=so[0]
						jvp.percent=so[1]
						jvp.quater=so[2]
						jvp.fiscal_year=so[3]
						jvp.amount=cstr(flt(jv[2])*flt(so[1])/flt(100))
						jvp.parent=jv[0]
						jvp.docstatus=1
						jvp.status='False'
						jvp.save()
						webnotes.conn.sql("update `tabJournal Voucher` set status='True' where name='%s'"%(jv[0]))
						webnotes.conn.sql("commit")
		self.calculate_variable()

	def calculate_variable(self):
		sales_persons=webnotes.conn.sql('select distinct sales_person from `tabSales Team`',as_list=1)
		sp_variable_pay={}
		if sales_persons:
			for person in sales_persons:
				sp_variable_pay[person[0]]=0.0
				fiscal_year=webnotes.conn.sql("select name from `tabFiscal Year`",as_list=1)
				if fiscal_year:
					for year in fiscal_year:
						i=1
						for qtr_month in range(i,5):
							month=self.months.get(cint(qtr_month))
							if month:
								i=i+3
								sales_persons_details=webnotes.conn.sql("""select sum(amount)
									from `tabVariable Pay Summary` where sales_person='%s' and fiscal_year='%s' and quater='%s' 
									and status='False'"""%(person[0],year[0],month),as_list=1)
								if sales_persons_details:
									for total_jv in sales_persons_details:
										target_details=self.target_all_details(person[0],year[0],month)
										if target_details:
											for detail in target_details:
												webnotes.conn.sql("update `tabVariable Pay Summary` set status='True' where sales_person='%s' and fiscal_year='%s' and quater='%s'"%(person[0],year[0],month))
												quater_target_amount=flt(detail[0])*flt(detail[1])/flt(100)
												quater_target_variable_pay=flt(detail[2])*flt(detail[1])/flt(100)
												sp_variable_pay[person[0]]+=flt(total_jv[0])*quater_target_variable_pay/quater_target_amount
				if sp_variable_pay[person[0]]:
					m=cint(self.to_date().month)
					spv=Document('Sales Person Variable Pay')
					spv.sales_person=person[0]
					spv.posting_date=nowdate()
					if self.fiscal_year:
						spv.fiscal_year=self.fiscal_year[0][0]
					spv.variable_pay=sp_variable_pay[person[0]]
					spv.month = '0'+cstr(m) if m in range(1,9) else m
					spv.status='False'
					spv.save()
		webnotes.conn.sql("commit")
