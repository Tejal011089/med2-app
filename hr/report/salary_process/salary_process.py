# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)

	return columns, data 

def get_columns():
	return ["Account No::120","CUR CODE::120","SOL ID:Link/Employee:120","CR DR::100","TRAN AMT:Currency:100","TRAN PART::100", "TRANS_DESC::120"]

def get_data(filters):
	cond = ''
	if filters.get("month"):
		cond = """ where month = month(str_to_date('%(month)s','%(b)s')) """%{'month':filters.get("month"), "b":"%b"}

	return webnotes.conn.sql("""select 
					bank_account_no, 'INR', 
					employee, 'C', 
					rounded_total, employee_name, 
					concat('By Sal ',MONTHNAME(STR_TO_DATE(month, '%(month_abbr)s')), ' ', year(now())) 
				from `tabSalary Slip` 
				%(cond)s"""%{'month_abbr': '%m', 'cond': cond},as_list=1)
