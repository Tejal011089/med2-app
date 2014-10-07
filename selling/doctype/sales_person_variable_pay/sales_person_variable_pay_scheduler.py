import webnotes
from webnotes.model.doc import Document
from webnotes.utils import now, cint,nowtime,cstr,nowtime
from datetime import datetime, timedelta
from selling.doctype.sales_person_variable_pay.sales_person_variable_pay import DocType

def create_variable_pay():
	date=datetime.now()
	print date
	if cint(date.day)==1:
		obj=DocType(None,None)
		if cint(date.month) in (1,4,7,10):
			obj.update_sales_person_eligibility()
		obj.update_jv()

