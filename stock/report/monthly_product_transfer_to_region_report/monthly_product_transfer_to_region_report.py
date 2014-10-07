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
        columns=["Month::150","Total Quantity::150","From Warehouse::150","To Warehouse::150"]
        return columns

def get_conditions(filters):
        conditions = ""
        return conditions

def get_details(filters):
        return  webnotes.conn.sql("""select date_format(a.creation,'%Y-%m') as month,sum(coalesce(b.qty,0)),b.s_warehouse,b.t_warehouse from `tabStock Entry`a,`tabStock Entry Detail`b where b.parent=a.name and s_warehouse='Head Office - MS' and purpose='Material Transfer' group by t_warehouse,month""",as_list=1)
