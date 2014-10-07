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
        columns=["Lead:Data:100","Lead Creation Date:Date:100","Opportunity::100","Opp from Lead::100","Opp from Customer::100" ,"Opp Creation Date:Date:100","Customer::100","Cust.From Lead::100","Cust.Creation Date::100","Quotation::100","Quo.From Lead::100","Quo.From Customer::100","Quo.Creation Date","Sales Order::100","SO From Quo.::100","SO Creation Date::100","IOF::100","IOF From SO::100","IOF Creation Date::100","IN::100","IN From IOF::100","IN Creation Date::100"]
        return columns

def get_conditions(filters):
        conditions = ""
        return conditions

def get_details(filters):
        return  webnotes.conn.sql("""select distinct a.name,date(a.creation),b.name,b.lead,b.customer,date(b.creation),c.name,c.lead_name,date(c.creation),d.name,d.lead,d.customer,date(d.creation),e.name,f.prevdoc_docname,date(e.creation),g.name,h.prevdoc_docname,date(g.creation),i.name,i.internal_order_no,date(i.creation) from `tabLead`a,`tabOpportunity`b,`tabCustomer`c ,`tabQuotation`d,`tabSales Order`e,`tabSales Order Item`f,`tabInternal Order Form`g,`tabInternal Order Item Details`h,`tabInstallation Note`i where (a.name=b.lead  or b.customer=c.name )and a.name=c.lead_name and (a.name=d.lead or c.name=d.customer) and d.name=f.prevdoc_docname and e.name=h.prevdoc_docname and g.name=i.internal_order_no """,as_list=1)
