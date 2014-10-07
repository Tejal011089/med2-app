#License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.utils import flt
sql = webnotes.conn.sql
from webnotes import _, msgprint
import datetime

def execute(filters=None):
        if not filters: filters = {}

        columns = get_columns()
        data = get_details(filters)
        #webnotes.errprint(data)
        return columns,data

def get_columns():
        columns=["Month::100","Sales Person::100","Total Sale::100","Purchase Cost::100","Total Expense::100","Total Commission::100" ,"Salary::100","Net Profit::100"]
        return columns

def get_conditions(filters):
        conditions = ""
        return conditions

def get_details(filters):
        return  webnotes.conn.sql("""select date,sales_person,sum(Total_sale) as Total_sale,sum(purchase_cost) as purchase_cost,sum(total_expense) as total_expense,sum(total_commission) as total_commission,(Salary) as Salary,sum(Total_sale)-(sum(purchase_cost)+(Salary)+sum(total_expense)+sum(total_commission)) as Net_Profit from(select date,sales_person,sum(purchase_cost) as purchase_cost,Total_sale,total_expense,total_commission,Salary from(select distinct date_format(st.creation,'%Y-%m') as date,so.name,st.sales_person,(soi.qty*pri.import_rate) as purchase_cost,(coalesce(st.allocated_amount,0)) as Total_sale,coalesce((select sum(coalesce(total_claimed_amount,0)) from `tabExpense Claim` where employee_name=st.sales_person),0) as total_expense,coalesce(so.total_commission,0) as total_commission,coalesce((select coalesce(ctc,0) from`tabSalary Structure` where employee_name=st.sales_person),0) as Salary from `tabSales Order` so ,`tabSales Team` st ,`tabSales Order Item` soi ,`tabPurchase Receipt` pr,`tabPurchase Receipt Item`pri where soi.parent=so.name and pri.parent=pr.name and so.name=st.parent and pri.item_code=soi.item_code and so.docstatus=1 )foo group by date,sales_person,name )foo2 group by date,sales_person,Salary """,as_list=1)
