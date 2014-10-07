# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.model.doc import addchild

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def get_dtl(self):
		self.doclist = self.doc.clear_table(self.doclist, 'edit_sms')
		webnotes.errprint("in edit fun")
		res=webnotes.conn.sql("select id,message_body from smslog where flag=0 and message_body like '#%#'")
		webnotes.errprint(res)
		for r in res:
			nl = addchild(self.doc, 'edit_sms', 'smslogeditchild', self.doclist)
			nl.sms_id =r[0]
			nl.message_edit =r[1]
			#webnotes.errprint(nl.sms_id)
		return "hi" 


	def on_update(self):
		from webnotes.model.bean import getlist
		from webnotes.utils import cstr
		#res=webnotes.conn.sql("select  ")
		for d in getlist(self.doclist, 'edit_sms'):
			#webnotes.errprint(d.sms_id)
			#webnotes.errprint(d.message_edit)
			#webnotes.errprint (" aaa----")
			aa="update smslog set message_body='"+cstr(d.message_edit)+"' where id="+cstr(d.sms_id)
			webnotes.conn.sql(aa)
