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
        columns=["Region::120","Employee::200" ,"Month::100","Total No.of Leads::120","Total No.of Converted Leads::180" ,"Ratio::100" ]
        return columns

def get_conditions(filters):
        conditions = ""
        return conditions

def get_details(filters):
        #conditions = get_conditions(filters)
        return  webnotes.conn.sql("""select territory,owner,creation,sum(opp_count) as opp_cnt,count(*) as mnt_cnt, (sum(opp_count)/count(*))*100 as ratio from (select a.territory,a.name,a.owner,date_format(a.creation,'%Y-%m') as creation,(select  count(*) from `tabOpportunity` b where b.lead=a.name) as opp_count from `tabLead` a )foo group by creation """,as_list=1)
