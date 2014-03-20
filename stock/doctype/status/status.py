# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
from webnotes.utils import cstr, cint, flt, comma_or, nowdate

import webnotes

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	#def on_update(self):
	#	qry=webnotes.conn.sql("""select priority from `tabStatus` """,as_list=1)
	#	webnotes.errprint(qry)
	#	a=self.doc.priority
	#	webnotes.errprint(a)
	#	t=qry.count([a])
	#	webnotes.errprint(t)
	#	if cint(t) == 2:
	#	#if [a] in qry:
	#		webnotes.errprint("in if loop")
	#		webnotes.msgprint("No Duplicate Priority at Status = '"+self.doc.status+"' ",raise_exception=1)
 
