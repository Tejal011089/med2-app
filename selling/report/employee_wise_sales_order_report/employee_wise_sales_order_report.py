# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
#from webnotes import _, msgprint
from webnotes.utils import flt
#sql = webnotes.conn.sql


from webnotes import _, msgprint

def execute(filters=None):
        if not filters: filters = {}

        columns = get_columns()
        data = get_details(filters)
        return columns,data

def get_columns():
        columns=["Region::100" ,"Employee::150","Sales Order No.::150","Order Date::100","OEM/Direct:Select:100", "Product::120" , "Amount::120","Sales Commission::120","Invoice Date::120" ]
        return columns

def get_conditions(filters):
        conditions = ""
        if filters.get("territory"):
            conditions += "and a.territory='%s'"%filters.get("territory")
        if filters.get("owner"):
            conditions += "and a.owner='%s'"%filters.get("owner")
        if filters.get("transaction_date"):
            conditions += "and a.transaction_date='%s'"%filters.get("transaction_date")
        if filters.get("creation"):
            conditions += "and soi.creation='%s'"%filters.get("creation")
        if filters.get("customer_type"):
            conditions += "and a.customer_type='%s'"%filters.get("customer_type")
        if filters.get("item_code"):
            conditions += "and x.item_code='%s'"%filters.get("item_code")
        if filters.get("net_total_export"):
            conditions += "and a.net_total_export='%s'"%filters.get("net_total_export")
        if filters.get("total_commission"):
            conditions += "and a.total_commission='%s'"%filters.get("total_commission")
        return conditions


def get_details(filters):
        conditions = get_conditions(filters)
        return  webnotes.conn.sql("""select a.territory,a.owner,a.name,a.transaction_date,a.customer_type,x.item_code, a.net_total_export,a.total_commission,date(soi.creation) from
`tabSales Order` a
left join (select item_code,parent from `tabAccessories Details` b union select item_code,parent from `tabSales Order Item` c ) x on x.parent=a.name
left join (select creation,sales_order from `tabSales Invoice Item` si where creation in(select min(creation) from `tabSales Invoice Item` where sales_order=si.sales_order)) soi on soi.sales_order=a.name 
order by owner,territory %s"""%conditions, as_list=1)
