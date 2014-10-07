# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
"""will be called by scheduler"""

import webnotes
from webnotes.utils import scheduler
	
def execute_all():
	"""
		* get support email
		* recurring invoice
	"""
	from selling.utils import fetch_sms
	print "fetch sms data"
	run_fn(fetch_sms)
	# pull emails
	from support.doctype.support_ticket.get_support_mails import get_support_mails
	#print "email support"
	run_fn(get_support_mails)
        #print "support email end"	
	from selling.utils import send_ticket_details
	from selling.utils import send_sales_details
	from selling.utils import send_isbpl_details
	from selling.utils import send_todays_material_details
	from selling.utils import send_low_stock_details
	import time
	ss=time.strftime("%H:%M:%S")
	aa=ss.split(':')
	print aa
	if aa[0]=='02':
		#print "aa =21"
		#print aa[0]
		if aa[1] >='00' and aa[1] <='03':
			#print "sales start"
			run_fn(send_sales_details)
			#print "sales end"
			run_fn(send_ticket_details)
			run_fn(send_isbpl_details)
			run_fn(send_todays_material_details)
			run_fn(send_low_stock_details)
			
	'''

	from hr.doctype.job_applicant.get_job_applications import get_job_applications
	run_fn(get_job_applications)

	from selling.doctype.lead.get_leads import get_leads
	run_fn(get_leads)

	from webnotes.utils.email_lib.bulk import flush
	run_fn(flush)
        '''
	from selling.utils import get_payment_followup
	run_fn(get_payment_followup)

	from selling.utils import get_escalation_for_supportticket
        run_fn(get_escalation_for_supportticket)
	
	
def execute_daily():
	from selling.utils import send_invoice_details
	import datetime
	ss=datetime.datetime.today().day
	print ss
	if ss==1 or ss==16 :
		print "in ss = 20"
		run_fn(send_invoice_details)

	from selling.utils import send_amccmc_details
	print "sending amc/cmc"
	run_fn(send_amccmc_details)
	
	from selling.doctype.sales_person_variable_pay.sales_person_variable_pay_scheduler import create_variable_pay
	run_fn(create_variable_pay)
	# event reminders
	
        from webnotes.utils.email_lib.bulk import send_bday
	print "sending bday ntfn"
        run_fn(send_bday)

        from webnotes.utils.email_lib.bulk import send_working
        print "sending working ntfn"
        run_fn(send_working)
        
        from webnotes.utils.email_lib.bulk import send_evluation
        print "sending evluation ntfn"
        run_fn(send_evluation)	
	'''
	from core.doctype.event.event import send_event_digest
	run_fn(send_event_digest)
	
	# clear daily event notifications
	from core.doctype.notification_count.notification_count import delete_notification_count_for
	delete_notification_count_for("Event")
	
	# run recurring invoices
	from accounts.doctype.sales_invoice.sales_invoice import manage_recurring_invoices
	run_fn(manage_recurring_invoices)

	# send bulk emails
	from webnotes.utils.email_lib.bulk import clear_outbox
	run_fn(clear_outbox)

	# daily backup
	from setup.doctype.backup_manager.backup_manager import take_backups_daily
	run_fn(take_backups_daily)

	# check reorder level
	from stock.utils import reorder_item
	run_fn(reorder_item)
	
	# email digest
	from setup.doctype.email_digest.email_digest import send
	run_fn(send)
	
	# auto close support tickets
	from support.doctype.support_ticket.support_ticket import auto_close_tickets
	run_fn(auto_close_tickets)
	'''


		
def execute_weekly():
	from setup.doctype.backup_manager.backup_manager import take_backups_weekly
	run_fn(take_backups_weekly)

	from selling.utils import send_oppt_details
	run_fn(send_oppt_details)

def execute_monthly():
	pass

def execute_hourly():
	from selling.utils import get_escalation_for_supportticket
	print "hourly ticket esclation"
	run_fn(get_escalation_for_supportticket)
	
def run_fn(fn):
	try:
		fn()
	except Exception, e:
		scheduler.log(fn.func_name)
