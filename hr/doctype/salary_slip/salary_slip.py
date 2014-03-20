# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
import calendar
from webnotes.utils import add_days, cint, cstr, flt, getdate, nowdate, _round
from webnotes.model.doc import make_autoname
from webnotes.model.bean import getlist
from webnotes.model.code import get_obj
from webnotes import msgprint, _
from webnotes.model.doc import addchild
from setup.utils import get_company_currency
import calendar
	
from utilities.transaction_base import TransactionBase
sql = webnotes.conn.sql

class DocType(TransactionBase):
	def __init__(self,doc,doclist=[]):
		self.doc = doc
		self.doclist = doclist
		
	def autoname(self):
		self.doc.name = make_autoname('Sal Slip/' +self.doc.employee + '/.#####') 

	def get_emp_and_leave_details(self):
		if self.doc.employee:
			self.get_leave_details()
			struct = self.check_sal_struct()
			if struct:
				self.pull_sal_struct(struct)

	def check_sal_struct(self):
		struct = webnotes.conn.sql("""select name from `tabSalary Structure` 
			where employee=%s and is_active = 'Yes'""", self.doc.employee)
		if not struct:
			msgprint("Please create Salary Structure for employee '%s'" % self.doc.employee)
			self.doc.employee = None
		return struct and struct[0][0] or ''

	def pull_sal_struct(self, struct):
		from hr.doctype.salary_structure.salary_structure import get_mapped_doclist
		self.doclist = get_mapped_doclist(struct, self.doclist)
		
	def pull_emp_details(self):
		emp = webnotes.conn.get_value("Employee", self.doc.employee, 
			["bank_name", "bank_ac_no", "esic_card_no", "pf_number"], as_dict=1)
		if emp:
			self.doc.bank_name = emp.bank_name
			self.doc.bank_account_no = emp.bank_ac_no
			self.doc.esic_no = emp.esic_card_no
			self.doc.pf_no = emp.pf_number

	def get_leave_details(self, lwp=None):
		if not self.doc.fiscal_year:
			self.doc.fiscal_year = webnotes.get_default("fiscal_year")
		if not self.doc.month:
			self.doc.month = "%02d" % getdate(nowdate()).month
			
		m = get_obj('Salary Manager').get_month_details(self.doc.fiscal_year, self.doc.month)
		holidays = self.get_holidays_for_employee(m)
		
		if not cint(webnotes.conn.get_value("HR Settings", "HR Settings",
			"include_holidays_in_total_working_days")):
				m["month_days"] -= len(holidays)
				if m["month_days"] < 0:
					msgprint(_("Bummer! There are more holidays than working days this month."),
						raise_exception=True)
			
		if not lwp:
			lwp = self.calculate_lwp(holidays, m)
		self.doc.total_days_in_month = m['month_days']
		self.doc.leave_without_pay = lwp
		payment_days = flt(self.get_payment_days(m)) - flt(lwp)
		self.doc.payment_days = payment_days > 0 and payment_days or 0
		

	def get_payment_days(self, m):
		payment_days = m['month_days']
		emp = webnotes.conn.sql("select date_of_joining, relieving_date from `tabEmployee` \
			where name = %s", self.doc.employee, as_dict=1)[0]
			
		if emp['relieving_date']:
			if getdate(emp['relieving_date']) > m['month_start_date'] and \
				getdate(emp['relieving_date']) < m['month_end_date']:
					payment_days = getdate(emp['relieving_date']).day
			elif getdate(emp['relieving_date']) < m['month_start_date']:
				webnotes.msgprint(_("Relieving Date of employee is ") + cstr(emp['relieving_date']
					+ _(". Please set status of the employee as 'Left'")), raise_exception=1)
				
			
		if emp['date_of_joining']:
			if getdate(emp['date_of_joining']) > m['month_start_date'] and \
				getdate(emp['date_of_joining']) < m['month_end_date']:
					payment_days = payment_days - getdate(emp['date_of_joining']).day + 1
			elif getdate(emp['date_of_joining']) > m['month_end_date']:
				payment_days = 0

		return payment_days
		
	def get_holidays_for_employee(self, m):
		holidays = webnotes.conn.sql("""select t1.holiday_date 
			from `tabHoliday` t1, tabEmployee t2 
			where t1.parent = t2.holiday_list and t2.name = %s 
			and t1.holiday_date between %s and %s""", 
			(self.doc.employee, m['month_start_date'], m['month_end_date']))
		if not holidays:
			holidays = webnotes.conn.sql("""select t1.holiday_date 
				from `tabHoliday` t1, `tabHoliday List` t2 
				where t1.parent = t2.name and ifnull(t2.is_default, 0) = 1 
				and t2.fiscal_year = %s
				and t1.holiday_date between %s and %s""", (self.doc.fiscal_year, 
					m['month_start_date'], m['month_end_date']))
		holidays = [cstr(i[0]) for i in holidays]
		return holidays

	def calculate_lwp(self, holidays, m):
		lwp = 0
		for d in range(m['month_days']):
			dt = add_days(cstr(m['month_start_date']), d)
			if dt not in holidays:
				leave = webnotes.conn.sql("""
					select t1.name, t1.half_day
					from `tabLeave Application` t1, `tabLeave Type` t2 
					where t2.name = t1.leave_type 
					and ifnull(t2.is_lwp, 0) = 1 
					and t1.docstatus = 1 
					and t1.employee = %s
					and %s between from_date and to_date
				""", (self.doc.employee, dt))
				if leave:
					lwp = cint(leave[0][1]) and (lwp + 0.5) or (lwp + 1)
		return lwp

	def check_existing(self):
		ret_exist = webnotes.conn.sql("""select name from `tabSalary Slip` 
			where month = %s and fiscal_year = %s and docstatus != 2 
			and employee = %s and name != %s""", 
			(self.doc.month, self.doc.fiscal_year, self.doc.employee, self.doc.name))
		if ret_exist:
			self.doc.employee = ''
			msgprint("Salary Slip of employee '%s' already created for this month" 
				% self.doc.employee, raise_exception=1)


	def validate(self):
		from webnotes.utils import money_in_words
		self.check_existing()
		
		if not (len(self.doclist.get({"parentfield": "earning_details"})) or 
			len(self.doclist.get({"parentfield": "deduction_details"}))):
				self.get_emp_and_leave_details()
		else:
			self.get_leave_details(self.doc.leave_without_pay)

		if not self.doc.net_pay:
			self.calculate_net_pay()
			
		company_currency = get_company_currency(self.doc.company)
		self.doc.total_in_words = money_in_words(self.doc.rounded_total, company_currency)

	def calculate_earning_total(self):
	        self.doc.gross_pay = flt(self.doc.arrear_amount) + flt(self.doc.leave_encashment_amount)
		s_date = e_date = ''
		        #webnotes.errprint("in sales target")
		if cint(self.doc.month)%3 == 0:
                	s_date, e_date = self.get_dates(cint(self.doc.month))
                #m=cint(self.doc.month)
              		#webnotes.errprint(m)
	        m_name=calendar.month_name[cint(self.doc.month)]
                webnotes.errprint(m_name)
                
		# if m==3 or m==6 or m==9 or m==12:

	 #                if  m==3:
	 #                        s_date, e_date = self.get_dates(m)
	 #                        # webnotes.errprint("in first")
  #       	                # s_date='2014-01-01'
  #               	        # e_date='2014-03-31'
  #                       	# webnotes.errprint(s_date)
	 #                        # webnotes.errprint(e_date)
  #       	        elif  m==6:
  #       	        	    s_date, e_date = self.get_dates(m)
  #               	        # webnotes.errprint("in second")
  #                       	# s_date='2014-04-01'
	 #                        # e_date='2014-06-30'
		# 		# webnotes.errprint(s_date)
  #               	        # webnotes.errprint(e_date)

	 #                elif  m==9:
	 #                	    s_date, e_date = self.get_dates(m)
  #       	                # webnotes.errprint("in third")
  #               	        # s_date='2014-07-01'
  #                       	# e_date='2014-09-30'
	 #                elif m==12:
	 #                	    s_date, e_date = self.get_dates(m)
        	                # webnotes.errprint("in forth")
                	        # s_date='2014-07-01'
                        	# e_date='2014-12-31'
			 #webnotes.errprint([select parent,target_amount ,variable_pay from `tabTarget Detail` where parent in  (select sales_person from `tabSales Team` where parent in 
                         #               (select name from `tabSales Order` where transaction_date between %s and %s  
                         #             group by sales_person)) ,(s_date,e_date)])
		if s_date and e_date:
			qry1=webnotes.conn.sql("""select parent,target_amount ,variable_pay from `tabTarget Detail` where parent in  (select sales_person from `tabSales Team` where parent in 
                                        (select name from `tabSales Order` where transaction_date between %s and %s
                                       group by sales_person)) """,(s_date,e_date) ,debug=1)
			webnotes.errprint(qry1)
                #list1=[]
               		for i in qry1:
				webnotes.errprint("in for loop")
				name=webnotes.conn.sql("""select employee from `tabSales Person` where name=%s """,i[0],as_list=1)
				webnotes.errprint(name)
		                if name[0][0] == self.doc.employee:
					webnotes.errprint(name[0][0])

                        #webnotes.errprint(i[0])                
		                       	qr=webnotes.conn.sql("""select distribution_id  from `tabSales Person` where name=%s""",i[0],as_list=1)
       	                #webnotes.errprint(qr)
               		        	if m_name=='January' or m_name=='February' or m_name=='March':
                       		        	month='January-March'
                        		elif m_name=='April' or m_name=='May' or m_name=='June':
       	                        		month='April-June'
					
	               	        	elif m_name=='July' or m_name=='August' or m_name=='September':
        	               	        	month='July-September'
                	        	else:
       	                	        	month='October-December'
              	        		webnotes.errprint(month)
					if qr:
						webnotes.errprint("percentage allocation")
		                       		qt=webnotes.conn.sql(""" select percentage_allocation/100 from `tabBudget Distribution Detail` where 
        	                               	        month=%s and parent=%s""",(month,qr[0][0]))
        		               		webnotes.errprint(qt[0][0])
                       #webnotes.errprint(qt[0][0]*i[1])
                		       		amt=qt[0][0]*i[1]
                       				webnotes.errprint(amt)
                       				qry=webnotes.conn.sql(""" select sum(allocated_amount) as amount from `tabSales Team` where parent in 
                               		       		(select name from `tabSales Order` where transaction_date between %s and %s and docstatus=1) 
                                    			and  sales_person=%s """,(s_date,e_date,i[0]))
	                       			webnotes.errprint(qry)
			#name=webnotes.conn.sql("""select employee from `tabSales Person` where name=%s """,i[0],as_list=1)
                        #webnotes.errprint(name[0][0])
                        #webnotes.errprint(["pay",i[2]])
						if qry:

	                	       			t= ((flt(qry[0][0])/amt)*100)/(100)
        		               			webnotes.errprint(t)
					#webnotes.msgprint(i[2])
                	       				pay= (i[2]/4)*t
					#webnotes.msgprint(pay)
							self.doc.variable_pay=pay
        	               				webnotes.errprint(self.doc.variable_pay)
	
	

		for d in self.doclist.get({"parentfield": "earning_details"}):
			if cint(d.e_depends_on_lwp) == 1:
				d.e_modified_amount = _round(flt(d.e_amount) * flt(self.doc.payment_days)
					/ cint(self.doc.total_days_in_month), 2)
			elif not self.doc.payment_days:
				d.e_modified_amount = 0
			else:
				d.e_modified_amount = d.e_amount
			self.doc.gross_pay += flt(d.e_modified_amount)
		self.doc.gross_pay +=flt(self.doc.variable_pay)

	def get_dates(self, month):
		from dateutil.relativedelta import relativedelta
		year_start_date, year_end_date = webnotes.conn.get_value("Fiscal Year", 
			self.doc.fiscal_year, ["year_start_date", "year_end_date"])
		
		increment = {
			3: 12,
			6: 3,
			9: 6,
			12: 9
		}.get(month)
		period_start_date = getdate(year_start_date) + relativedelta(months=(increment-3))
		period_end_date = getdate(year_start_date) + relativedelta(months=increment, days=-1)

		return period_start_date, period_end_date


	def calculate_ded_total(self):
		self.doc.total_deduction = 0
		qry=webnotes.conn.sql(" select name from `tabEmployee Loan` where employee_name=%s", self.doc.employee ,as_list=1)
		#webnotes.errprint(qry)
		if len(qry)!=0:
			qr=webnotes.conn.sql("select date_of_installment from `tabLoan Installment Details` where parent=%s",qry[0][0],as_list=1)
			#webnotes.errprint(qr)
			r=0
			for i in qr:
				t=getdate(i[0]).month
				#webnotes.errprint(t)
				#webnotes.errprint(self.doc.month)
				webnotes.errprint(t == cint(self.doc.month))
				if t == cint(self.doc.month):
					webnotes.errprint("in if loop")
					#webnotes.errprint(getdate(i[0]))
					q=webnotes.conn.sql("select amount_to_be_paid from `tabLoan Installment Details` where date_of_installment=%s and parent=%s",(getdate(i[0]),qry[0][0]),as_list=1)
					w=webnotes.conn.sql("Update `tabLoan Installment Details` set status='Paid' where date_of_installment=%s",getdate(i[0]))
					#webnotes.errprint(q)
					r=q[0][0]
					#ch = addchild(self.doc, 'deduction_details', 
					#'Salary Slip Deduction', self.doclist)
					#ch.d_type='Loan'
					#ch.d_amount=r
					#ch.d_modified_amount=r
					#ch.save(new=1)						
					self.doc.loan_amount=r
					#webnotes.errprint(ch) 
					#return{
					#	'd_type':ch.d_type
						#'ch.d_amount':r
						#'ch.d_modified_amount':r
					#}
					#webnotes.errprint(self.doc.loan_amount)
		m=0.0
		for d in getlist(self.doclist, 'deduction_details'):
			if cint(d.d_depends_on_lwp) == 1:
				d.d_modified_amount = _round(flt(d.d_amount) * flt(self.doc.payment_days) 
					/ cint(self.doc.total_days_in_month), 2)
			elif not self.doc.payment_days:
				d.d_modified_amount = 0
			else:
				d.d_modified_amount = d.d_amount
			m+=flt(d.d_modified_amount)
		if self.doc.loan_amount:
			ch = addchild(self.doc, 'deduction_details', 'Salary Slip Deduction', self.doclist)
               		ch.d_type='Loan'
                	ch.d_amount=cstr(self.doc.loan_amount)
                	ch.d_modified_amount=cstr(self.doc.loan_amount)
			ch.parent=self.doc.name
			ch.parentfield='deduction_details'
			ch.parenttype='Salary Slip'
		self.doc.total_deduction= m+flt(self.doc.loan_amount)
		
	def calculate_net_pay(self):
		self.calculate_earning_total()
		self.calculate_ded_total()
		self.doc.net_pay = flt(self.doc.gross_pay) - flt(self.doc.total_deduction)
		self.doc.rounded_total = _round(self.doc.net_pay)		

	def on_submit(self):
		if(self.doc.email_check == 1):			
			self.send_mail_funct()
			

	def send_mail_funct(self):	 
		from webnotes.utils.email_lib import sendmail
		receiver = webnotes.conn.get_value("Employee", self.doc.employee, "company_email")
		if receiver:
			subj = 'Salary Slip - ' + cstr(self.doc.month) +'/'+cstr(self.doc.fiscal_year)
			earn_ret=webnotes.conn.sql("""select e_type, e_modified_amount from `tabSalary Slip Earning` 
				where parent = %s""", self.doc.name)
			ded_ret=webnotes.conn.sql("""select d_type, d_modified_amount from `tabSalary Slip Deduction` 
				where parent = %s""", self.doc.name)
		 
			earn_table = ''
			ded_table = ''
			if earn_ret:			
				earn_table += "<table cellspacing=5px cellpadding=5px width='100%%'>"
				
				for e in earn_ret:
					if not e[1]:
						earn_table += '<tr><td>%s</td><td align="right">0.00</td></tr>' % cstr(e[0])
					else:
						earn_table += '<tr><td>%s</td><td align="right">%s</td></tr>' \
							% (cstr(e[0]), cstr(e[1]))
				earn_table += '</table>'
			
			if ded_ret:
			
				ded_table += "<table cellspacing=5px cellpadding=5px width='100%%'>"
				
				for d in ded_ret:
					if not d[1]:
						ded_table +='<tr><td">%s</td><td align="right">0.00</td></tr>' % cstr(d[0])
					else:
						ded_table +='<tr><td>%s</td><td align="right">%s</td></tr>' \
							% (cstr(d[0]), cstr(d[1]))
				ded_table += '</table>'
			
			letter_head = webnotes.conn.get_value("Letter Head", {"is_default": 1, "disabled": 0}, 
				"content")
			
			msg = '''<div> %s <br>
			<table cellspacing= "5" cellpadding="5"  width = "100%%">
				<tr>
					<td width = "100%%" colspan = "2"><h4>Salary Slip</h4></td>
				</tr>
				<tr>
					<td width = "50%%"><b>Employee Code : %s</b></td>
					<td width = "50%%"><b>Employee Name : %s</b></td>
				</tr>
				<tr>
					<td width = "50%%">Month : %s</td>
					<td width = "50%%">Fiscal Year : %s</td>
				</tr>
				<tr>
					<td width = "50%%">Department : %s</td>
					<td width = "50%%">Branch : %s</td>
				</tr>
				<tr>
					<td width = "50%%">Designation : %s</td>
					<td width = "50%%">Grade : %s</td>
				</tr>
				<tr>				
					<td width = "50%%">Bank Account No. : %s</td>
					<td  width = "50%%">Bank Name : %s</td>
				
				</tr>
				<tr>
					<td  width = "50%%">Arrear Amount : <b>%s</b></td>
					<td  width = "50%%">Payment days : %s</td>
				
				</tr>
			</table>
			<table border="1px solid #CCC" width="100%%" cellpadding="0px" cellspacing="0px">
				<tr>
					<td colspan = 2 width = "50%%" bgcolor="#CCC" align="center">
						<b>Earnings</b></td>
					<td colspan = 2 width = "50%%" bgcolor="#CCC" align="center">
						<b>Deductions</b></td>
				</tr>
				<tr>
					<td colspan = 2 width = "50%%" valign= "top">%s</td>
					<td colspan = 2 width = "50%%" valign= "top">%s</td>
				</tr>
			</table>
			<table cellspacing= "5" cellpadding="5" width = '100%%'>
				<tr>
					<td width = '25%%'><b>Gross Pay :</b> </td>
					<td width = '25%%' align='right'>%s</td>
					<td width = '25%%'><b>Total Deduction :</b></td>
					<td width = '25%%' align='right'> %s</td>
				</tr>
				<tr>
					<tdwidth='25%%'><b>Net Pay : </b></td>
					<td width = '25%%' align='right'><b>%s</b></td>
					<td colspan = '2' width = '50%%'></td>
				</tr>
				<tr>
					<td width='25%%'><b>Net Pay(in words) : </td>
					<td colspan = '3' width = '50%%'>%s</b></td>
				</tr>
			</table></div>''' % (cstr(letter_head), cstr(self.doc.employee), 
				cstr(self.doc.employee_name), cstr(self.doc.month), cstr(self.doc.fiscal_year), 
				cstr(self.doc.department), cstr(self.doc.branch), cstr(self.doc.designation), 
				cstr(self.doc.grade), cstr(self.doc.bank_account_no), cstr(self.doc.bank_name), 
				cstr(self.doc.arrear_amount), cstr(self.doc.payment_days), earn_table, ded_table, 
				cstr(flt(self.doc.gross_pay)), cstr(flt(self.doc.total_deduction)), 
				cstr(flt(self.doc.net_pay)), cstr(self.doc.total_in_words))

			sendmail([receiver], subject=subj, msg = msg)
		else:
			msgprint("Company Email ID not found, hence mail not sent")
