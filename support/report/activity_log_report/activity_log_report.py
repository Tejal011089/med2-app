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
	
	#webnotes.errprint(data)

        return columns,data

def get_columns():
        columns=["Activity ID::100","Activity Type::100","Activity Date::100","Activity Time::100","Activity SubType::100","Sender Phone No::100","Emp ID::100","Client Name::100","Amount::150","Place::100","Barcode::100","IR NO::100","Product Name::100","Payment Type::100","Payment Mode::100","Cheque No::100","Cheque Bank::100","Cheque Status::100","Service Call Type::100","Phone NO::100","Email File Name::100","Entry Type::100"]
        return columns

def get_details(filters):
    # pass
        # conditions = get_conditions(filters)
        return  webnotes.conn.sql("""(select activity_id,activity_type,activity_date,activity_time,activity_subtype,sender_phone_no,emp_id,client_name,amount,place,barcode,ir_no,product_name,payment_type,payment_mode,cheque_no,cheque_bank,cheque_status,service_call_type,phone_no,email_file_name,entry_type from `tabActivity Data` limit 500) UNION (SELECT '', '', '', '','','', '', '',concat('Total =', SUM(amount)), '','', '', '', '', '', '', '', '', '', '', '', '' FROM `tabActivity Data`) """, as_list=1)

	#return [[]]

