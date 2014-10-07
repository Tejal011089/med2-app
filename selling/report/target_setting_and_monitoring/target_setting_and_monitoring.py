from __future__ import unicode_literals
import webnotes
from webnotes.utils import flt,cint
import time
import datetime
import calendar
from webnotes.utils import nowdate, nowtime, cstr, flt, now, getdate, add_months
def execute(filters=None):
        if not filters: filters = {}
        columns = get_columns()
        data = get_plan_details(filters)
        return columns, data


def get_columns():
        return ["Sales Person:Link/Sales Person:90", "Annual Target Amount:Float:170","Annual Variable Pay:Float:120","Target For Current Querter:Float:120","Employee Id:Link/Employee:120","Current Quarter Percentage Allocation:Float:120","Querterly Amount Achieved:Float:120"," Quarter Variable Pay:Float:120"]

def get_plan_details(filters):

	if filters.get("from_date") and filters.get("to_date"):

	#webnotes.errprint(filters.get("to_date"))
		s_date = getdate(filters.get("from_date"))
		e_date = getdate(filters.get("to_date"))
	#webnotes.errprint(s_date)
	#webnotes.errprint(e_date)
	#s=time.strftime("%d-%m-%Y")
	#import datetime

		month =cint(datetime.datetime.now().strftime("%m"))
		webnotes.errprint(month)
		m_name=calendar.month_name[month]

	else:
		webnotes.msgprint("First enter the Month ,From Date and To Date for the querter of which you want to see a report")
	
	if s_date and e_date:
		webnotes.errprint(type(s_date))
                qry1=webnotes.conn.sql("""select parent,target_amount,variable_pay from `tabTarget Detail` where parent in (select sales_person from `tabSales Team` where parent in (select name from `tabSales Order` where transaction_date between '%s' and '%s' ) group by sales_person) """%(s_date,e_date),as_list=1,debug=1)
                webnotes.errprint(qry1)

	#webnotes.errprint(qry1)
		final=[]
		for i in qry1:
			name=webnotes.conn.sql("""select employee from `tabSales Person` where 
		 			name=%s """,i[0],as_list=1)                                             
	 #webnotes.errprint(name)
	 #qry1.append(name[0][0])
	 #webnotes.errprint(qry1)
		 
		 	qr=webnotes.conn.sql("""select distribution_id  from `tabSales Person` where name=%s""",i[0],as_list=1)
		 	if m_name=='January' or m_name=='February' or m_name=='March':
                        	month='January-March'
				webnotes.errprint(month)
                 	elif m_name=='April' or m_name=='May' or m_name=='June':
                        	month='April-June'
                 	elif m_name=='July' or m_name=='August' or m_name=='September':
                        	month='July-September'
                 	else:
	                	month='October-December'
			if qr:

			 	 qt=webnotes.conn.sql(""" select percentage_allocation from `tabBudget Distribution Detail` where 
	                                                month=%s and parent=%s""",(month,qr[0][0]))
		 #qry1.append(qt[0][0])
		 #webnotes.errprint(qry1)
				 amt=(qt[0][0]/100)*i[1]
				 #webnotes.errprint(amt)
				 qry=webnotes.conn.sql(""" select sum(allocated_amount) as amount from `tabSales Team` where parent in 
                	                               (select name from `tabSales Order` where transaction_date between %s and %s and docstatus=1) 
                        	                        and  sales_person=%s """,(s_date,e_date,i[0]))
		 #qry1.append(qry[0][0])
		 #webnotes.errprint(qry1)
				 t= ((flt(qry[0][0])/flt(amt))*100)/100
				 pay= (i[2]/4)*t
				 webnotes.errprint(i)
				 i.append(amt)
				 webnotes.errprint(i)
				 i.append(name[0][0])
			         i.append(qt[0][0])
	        		 i.append(qry[0][0])
				 i.append(pay)
				 final.append(i)
	         #webnotes.errprint(i)
		 #list1=['Sales Person','Target Amount','Variable Pay','Employee','Percentage Allocation']
	#webnotes.errprint(qry1)
		return final
