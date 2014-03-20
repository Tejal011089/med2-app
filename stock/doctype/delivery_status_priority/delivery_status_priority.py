# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
from webnotes.model.bean import getlist

import webnotes

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	
	def on_update(self):
		#webnotes.errprint("in update")
		for m in getlist(self.doclist, 'delivery_tracking'):
			#webnotes.errprint("in for loop")
			if m.priority==0:
				webnotes.msgprint("Priority should be greater than zero",raise_exception=1)
        #       qry=webnotes.conn.sql("""select priority from `tabDelivery Tracking` """,as_list=1)
        #        webnotes.errprint(qry)
        #        #a=self.doc.priority
        #        #webnotes.errprint(a)
        #        t=qry.count([a])
        #        webnotes.errprint(t)
        #        if cint(t) == 2:
        #        #if [a] in qry:
        #                webnotes.errprint("in if loop")
        #                webnotes.msgprint("No Duplicate Priority at Status = '"+self.doc.status+"' ",raise_exception=1)


	#def get_delivery_details(self, status):
	#	webnotes.errprint("in details")
	#	webnotes.errprint(["select priority from `tabStatus` where status=%s",status])
	#	qry=webnotes.conn.sql("select priority from `tabStatus` where status=%s",status,as_list=1)
	#	webnotes.errprint(qry)
	#	return{
	#		'priority': qry[0][0]
	#	}
