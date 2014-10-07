# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
from webnotes.utils import cstr, cint, decode_dict, today
from webnotes.utils.email_lib import sendmail		
from webnotes.utils.email_lib.receive import POP3Mailbox
from core.doctype.communication.communication import make

class SupportMailbox(POP3Mailbox):	
	def setup(self, args=None):
		print "in setup fun"
		self.email_settings = webnotes.doc("Email Settings", "Email Settings")
		self.settings = args or webnotes._dict({
			"use_ssl": self.email_settings.support_use_ssl,
			"host": self.email_settings.support_host,
			"username": self.email_settings.support_username,
			"password": self.email_settings.support_password
		})
		
	def process_message(self, mail):
		print "process messages"
		if mail.from_email == self.email_settings.fields.get('support_email'):
			return
		thread_id = mail.get_thread_id()
		new_ticket = False

		if not (thread_id and webnotes.conn.exists("Support Ticket", thread_id)):
			new_ticket = True
		
		ticket = add_support_communication(mail.subject, mail.content, mail.from_email,
			docname=None if new_ticket else thread_id, mail=mail)
			
		if new_ticket and cint(self.email_settings.send_autoreply) and \
			"mailer-daemon" not in mail.from_email.lower():
				self.send_auto_reply(ticket.doc)

	def send_auto_reply(self, d):
		signature = self.email_settings.fields.get('support_signature') or ''
		response = self.email_settings.fields.get('support_autoreply') or ("""
A new Ticket has been raised for your query. If you have any additional information, please
reply back to this mail.
		
We will get back to you as soon as possible
----------------------
Original Query:

""" + d.description + "\n----------------------\n" + cstr(signature))

		sendmail(\
			recipients = [cstr(d.raised_by)], \
			sender = cstr(self.email_settings.fields.get('support_email')), \
			subject = '['+cstr(d.name)+'] ' + cstr(d.subject), \
			msg = cstr(response))
		
def get_support_mails():
	print "in get supoo fun"
	if cint(webnotes.conn.get_value('Email Settings', None, 'sync_support_mails')):
		SupportMailbox()
		
def add_support_communication(subject, content, sender, docname=None, mail=None):
	print "get suport com fun 2"
	qr="select customer,employee_id from `tabInstallation Note` where product_barcode='"+subject+"'"
	print qr
        res=webnotes.conn.sql(qr)
        print res
	'''
        w="select status,user_id from `tabEmployee` where name='%s'"%(res[0][1]);
	print w
        t=webnotes.conn.sql(w)
	print t
	q=" select territory from `tabCustomer` where name='%s'"%(res[0][0]);
 	print q
        r=webnotes.conn.sql(q)
	print r
       	w=" select parent from `tabDefaultValue` where  defkey = '%s' and defvalue = '%s'"%('territory',r[0][0])
        print w
	a=webnotes.conn.sql(w)
	print a
	if t[0][0] != 'Left':
		assigned_to=t[0][1]
		assigned_to_higher_level=a[0][0]
	else:
		assigned_to=a[0][0]
		assigned_to_higher_level=a[0][0]
		
	print "if else end"
	'''
	if docname:
		print "if"
		ticket = webnotes.bean("Support Ticket", docname)
		ticket.doc.status = 'Open'
		ticket.ignore_permissions = True
		ticket.doc.save()
		webnotes.conn.commit()
	else:
		print "else"
		assigned_to= None
		assigned_to_higher_level= None
		#print subject
		qr="select customer,employee_id from `tabInstallation Note` where product_barcode='%s'"%(subject);
        	res=webnotes.conn.sql(qr)
        	#print res
        	if res:
        		w="select status,user_id from `tabEmployee` where name='%s'"%(res[0][1]);
        		t=webnotes.conn.sql(w)
        		#print t
        		q=" select territory,customer_name from `tabCustomer` where name='%s'"%(res[0][0]);
        		r=webnotes.conn.sql(q)
        		#print r
        		if r:
        				w=" select parent from `tabDefaultValue` where  defkey = '%s' and defvalue = '%s'"%('territory',r[0][0])
       					a=webnotes.conn.sql(w)
       					#print a
       			if t[0][0] == 'Left':
				assigned_to=a[0][0]
                                assigned_to_higher_level=a[0][0]
				
			else:
                                assigned_to=t[0][1]
                                assigned_to_higher_level=a[0][0]
                from webnotes.model.doc import Document
        	a= Document('Support Ticket')
        	a.subject=subject
        	a.raised_by=sender
        	a.description=content
		a.territory=r[0][0]
        	a.customer=res[0][0]
		a.customer_name=r[0][1]
        	a.assigned_to_higher_level=assigned_to_higher_level
        	a.assigned_to=assigned_to
        	a.status='Open'
        	a.save(new=1)
		webnotes.conn.commit()
    	return a		
