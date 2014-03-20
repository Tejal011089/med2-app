# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
from webnotes import _, throw
from webnotes.utils import flt, cint
from webnotes.utils import load_json, nowdate, cstr
from webnotes.model.code import get_obj
from webnotes.model.doc import Document
from webnotes import msgprint
from webnotes.model.bean import getlist, copy_doclist
#from webnotes.model.code import get_obj
from webnotes.model.bean import getlist, copy_doclist
from datetime import datetime, timedelta,date
from webnotes.utils.email_lib import sendmail

import json

def get_customer_list(doctype, txt, searchfield, start, page_len, filters):
	if webnotes.conn.get_default("cust_master_name") == "Customer Name":
		fields = ["name", "customer_group", "territory"]
	else:
		fields = ["name", "customer_name", "customer_group", "territory"]
		
	return webnotes.conn.sql("""select %s from `tabCustomer` where docstatus < 2 
		and (%s like %s or customer_name like %s) order by 
		case when name like %s then 0 else 1 end,
		case when customer_name like %s then 0 else 1 end,
		name, customer_name limit %s, %s""" % 
		(", ".join(fields), searchfield, "%s", "%s", "%s", "%s", "%s", "%s"), 
		("%%%s%%" % txt, "%%%s%%" % txt, "%%%s%%" % txt, "%%%s%%" % txt, start, page_len))
		
@webnotes.whitelist()
def get_item_details(args):
	"""
		args = {
			"item_code": "",
			"warehouse": None,
			"customer": "",
			"conversion_rate": 1.0,
			"selling_price_list": None,
			"price_list_currency": None,
			"plc_conversion_rate": 1.0
		}
	"""

	if isinstance(args, basestring):
		args = json.loads(args)
	args = webnotes._dict(args)
	
	if args.barcode:
		args.item_code = _get_item_code(barcode=args.barcode)
	elif not args.item_code and args.serial_no:
		args.item_code = _get_item_code(serial_no=args.serial_no)
	
	item_bean = webnotes.bean("Item", args.item_code)
	
	_validate_item_details(args, item_bean.doc)
	
	meta = webnotes.get_doctype(args.doctype)

	# hack! for Sales Order Item
	warehouse_fieldname = "warehouse"
	if meta.get_field("reserved_warehouse", parentfield=args.parentfield):
		warehouse_fieldname = "reserved_warehouse"
	
	out = _get_basic_details(args, item_bean, warehouse_fieldname)
	
	if meta.get_field("currency"):
		out.base_ref_rate = out.basic_rate = out.ref_rate = out.export_rate = 0.0
		
		if args.selling_price_list and args.price_list_currency:
			out.update(_get_price_list_rate(args, item_bean, meta))
		
	out.update(_get_item_discount(out.item_group, args.customer))
	
	if out.get(warehouse_fieldname):
		out.update(get_available_qty(args.item_code, out.get(warehouse_fieldname)))
	
	out.customer_item_code = _get_customer_item_code(args, item_bean)
	
	if cint(args.is_pos):
		pos_settings = get_pos_settings(args.company)
		if pos_settings:
			out.update(apply_pos_settings(pos_settings, out))
		
	if args.doctype in ("Sales Invoice", "Delivery Note"):
		if item_bean.doc.has_serial_no == "Yes" and not args.serial_no:
			out.serial_no = _get_serial_nos_by_fifo(args, item_bean)
		
	return out

def _get_serial_nos_by_fifo(args, item_bean):
	return "\n".join(webnotes.conn.sql_list("""select name from `tabSerial No` 
		where item_code=%(item_code)s and warehouse=%(warehouse)s and status='Available' 
		order by timestamp(purchase_date, purchase_time) asc limit %(qty)s""", {
			"item_code": args.item_code,
			"warehouse": args.warehouse,
			"qty": cint(args.qty)
		}))

def _get_item_code(barcode=None, serial_no=None):
	if barcode:
		input_type = "Barcode"
		item_code = webnotes.conn.sql_list("""select name from `tabItem` where barcode=%s""", barcode)
	elif serial_no:
		input_type = "Serial No"
		item_code = webnotes.conn.sql_list("""select item_code from `tabSerial No` 
			where name=%s""", serial_no)
			
	if not item_code:
		throw(_("No Item found with ") + input_type + ": %s" % (barcode or serial_no))
	
	return item_code[0]
	
def _validate_item_details(args, item):
	from utilities.transaction_base import validate_item_fetch
	validate_item_fetch(args, item)
	
	# validate if sales item or service item
	if args.order_type == "Maintenance":
		if item.is_service_item != "Yes":
			throw(_("Item") + (" %s: " % item.name) + 
				_("not a service item.") +
				_("Please select a service item or change the order type to Sales."))
		
	elif item.is_sales_item != "Yes":
		throw(_("Item") + (" %s: " % item.name) + _("not a sales item"))
			
def _get_basic_details(args, item_bean, warehouse_fieldname):
	item = item_bean.doc
	
	from webnotes.defaults import get_user_default_as_list
	user_default_warehouse_list = get_user_default_as_list('warehouse')
	user_default_warehouse = user_default_warehouse_list[0] \
		if len(user_default_warehouse_list)==1 else ""
	
	out = webnotes._dict({
			"item_code": item.name,
			"description": item.description_html or item.description,
			warehouse_fieldname: user_default_warehouse or item.default_warehouse \
				or args.get(warehouse_fieldname),
			"income_account": item.default_income_account or args.income_account \
				or webnotes.conn.get_value("Company", args.company, "default_income_account"),
			"expense_account": item.purchase_account or args.expense_account \
				or webnotes.conn.get_value("Company", args.company, "default_expense_account"),
			"cost_center": item.default_sales_cost_center or args.cost_center,
			"qty": 1.0,
			"export_amount": 0.0,
			"amount": 0.0,
			"batch_no": None,
			"item_tax_rate": json.dumps(dict(([d.tax_type, d.tax_rate] for d in 
				item_bean.doclist.get({"parentfield": "item_tax"})))),
		})
	
	for fieldname in ("item_name", "item_group", "barcode", "brand", "stock_uom"):
		out[fieldname] = item.fields.get(fieldname)
			
	return out
	
def _get_price_list_rate(args, item_bean, meta):
	ref_rate = webnotes.conn.sql("""select ref_rate from `tabItem Price` 
		where price_list=%s and item_code=%s and selling=1""", 
		(args.selling_price_list, args.item_code), as_dict=1)

	if not ref_rate:
		return {}
	
	# found price list rate - now we can validate
	from utilities.transaction_base import validate_currency
	validate_currency(args, item_bean.doc, meta)
	
	return {"ref_rate": flt(ref_rate[0].ref_rate) * flt(args.plc_conversion_rate) / flt(args.conversion_rate)}
	
def _get_item_discount(item_group, customer):
	parent_item_groups = [x[0] for x in webnotes.conn.sql("""SELECT parent.name 
		FROM `tabItem Group` AS node, `tabItem Group` AS parent 
		WHERE parent.lft <= node.lft and parent.rgt >= node.rgt and node.name = %s
		GROUP BY parent.name 
		ORDER BY parent.lft desc""", (item_group,))]
		
	discount = 0
	for d in parent_item_groups:
		res = webnotes.conn.sql("""select discount, name from `tabCustomer Discount` 
			where parent = %s and item_group = %s""", (customer, d))
		if res:
			discount = flt(res[0][0])
			break
			
	return {"adj_rate": discount}

def send_sms(msg,sender_no):
	       ss = get_obj('SMS Settings', 'SMS Settings', with_children=1)
               webnotes.errprint("In send SMS ")
	       webnotes.errprint(ss)
	       #return ss
               args = {}
               #msg="Ticket Created"
               for d in getlist(ss.doclist, 'static_parameter_details'):
                        args[d.parameter] = d.value
               sms_url=webnotes.conn.get_value('SMS Settings', None, 'sms_gateway_url')
               msg_parameter=webnotes.conn.get_value('SMS Settings', None, 'message_parameter')
               receiver_parameter=webnotes.conn.get_value('SMS Settings', None, 'receiver_parameter')
               url = sms_url +"?user="+ args["user"] +"&senderID="+ args["sender ID"] +"&receipientno="+ sender_no +"\
                               &dcs="+ args["dcs"]+ "&msgtxt=" + msg +"&state=" +args["state"]
               webnotes.errprint(url)
               import requests
               r = requests.get(url)


def send_email(email,msg):
                webnotes.errprint("in email")
                #webnotes.msgprint(email)
                from webnotes.utils.email_lib import sendmail
                sendmail(email, subject="Payment Due Details", msg = msg)

@webnotes.whitelist()
def get_available_qty(item_code, warehouse):
	return webnotes.conn.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, 
		["projected_qty", "actual_qty"], as_dict=True) or {}
		
def _get_customer_item_code(args, item_bean):
	customer_item_code = item_bean.doclist.get({"parentfield": "item_customer_details",
		"customer_name": args.customer})
	
	return customer_item_code and customer_item_code[0].ref_code or None
	
def get_pos_settings(company):
	pos_settings = webnotes.conn.sql("""select * from `tabPOS Setting` where user = %s 
		and company = %s""", (webnotes.session['user'], company), as_dict=1)
	
	if not pos_settings:
		pos_settings = webnotes.conn.sql("""select * from `tabPOS Setting` 
			where ifnull(user,'') = '' and company = %s""", company, as_dict=1)
			
	return pos_settings and pos_settings[0] or None
	
def apply_pos_settings(pos_settings, opts):
	out = {}
	
	for fieldname in ("income_account", "cost_center", "warehouse", "expense_account"):
		if not opts.get(fieldname):
			out[fieldname] = pos_settings.get(fieldname)
			
	if out.get("warehouse"):
		out["actual_qty"] = get_available_qty(opts.item_code, out.get("warehouse")).get("actual_qty")
	
	return out

@webnotes.whitelist(allow_guest=True)
def get_installation_note(customer,emp_id,_type='POST'):
	#return "hello "+customer
	qr="select customer_name from `tabCustomer` where customer_name="+customer+" "
	res=webnotes.conn.sql(qr)
	#return res
	from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
	today = nowdate()
	qry="select name from `tabFiscal Year` where is_fiscal_year_closed='No'"
	res1=webnotes.conn.sql(qry)
	#return res1[0][0]
	from webnotes.model.doc import Document
	import time
	if res :
		d= Document('Installation Note')
		d.customer=customer[1:-1]
		d.customer_name=customer[1:-1]
		d.inst_time=time.strftime("%H:%M:%S")
		d.inst_date=today
		d.employee_id=emp_id[1:-1]
		return d.employee_id
		d.fiscal_year=res1[0][0]
		d.company='medsynaptic'
		d.territory='India'
		d.customer_group='Individual'
		#return d.fiscal_year
		d.save()
		webnotes.conn.commit()
	        return d.name	
	else:
		d= Document('Customer')
		d.customer_name=customer[1:-1]
		d.customer_type='Individual'
		d.customer_group='Individual'
		d.territory='India'
		d.save()
		webnotes.conn.commit()
		c= Document('Installation Note')
		c.customer=customer[1:-1]
		c.inst_time=time.strftime("%H:%M:%S")
                c.inst_date=today
		c.fiscal_year=res1[0][0]
		c.employee_id=emp_id[1:-1]
                c.company='Medsynaptic'
                c.territory='India'
		c.customer_group='Individual'
		c.save()
		webnotes.conn.commit()
	        return c.name

@webnotes.whitelist(allow_guest=True)
def get_customer_issue(installationname,sender_no,message,_type='POST'):
		#return installationname[1:-1]
		#sender_no1=sender_no[-11:]
		
		qr="select customer,employee_id from `tabInstallation Note` where name='"+installationname[1:-1]+"' "
        	res=webnotes.conn.sql(qr)
        	#return qr
		x="select customer_name from `tabCustomer` where customer_no='"+sender_no[1:-1]+"' "
		y=webnotes.conn.sql(x)
		#return x
		if y == None:
		
			z="select user_id from `tabEmployee` where cell_number="+sender_no[1:-1]+""	
			m=webnotes.conn.sql(z)
			#return m
		w="select status,user_id from `tabEmployee` where name='%s'"%(res[0][1]);
		t=webnotes.conn.sql(w)
		#return t
		from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
		today = nowdate()
		qry="select name from `tabFiscal Year` where is_fiscal_year_closed='No'"
        	res1=webnotes.conn.sql(qry)
	
		q=" select territory from `tabCustomer` where name='%s'"%(res[0][0]);

		r=webnotes.conn.sql(q)	
	 	w=" select parent from `tabDefaultValue` where  defkey = '%s' and defvalue = '%s'"%('territory',r[0][0])
		a=webnotes.conn.sql(w)
		#return a
		from webnotes.model.doc import Document
		import time
	
    		#if res :
        	d = Document('Support Ticket')
		d.opening_time=time.strftime("%H:%M:%S")
		if y:
			d.raised_by=y[0][0]
		elif z:
			d.raised_by=z[0][0]
		else:
			d.raised_by=sender_no1[-11:]
        	d.subject=installationname[1:-1]
		d.customer_name=res[0][0]
		d.customer=res[0][0]
		d.territory=r[0][0]
		d.status='Open'
		#d.customer_group='Individual'
		d.opening_date=today
        	#d.fiscal_year=res1[0][0]
        	d.company='medsynaptic'
        	d.territory=r[0][0]
		#d.raised_by=res[0][1]
		if t[0][0] =='Active':
			#return t[0][1]
			d.assigned_to=t[0][1]
			d.assigned_to_higher_level=a[0][0]
		else:
			d.assigned_to=a[0][0]
			d.assigned_to_higher_level=a[0][0]
		
		#d.assigned_to_higher_level=a[0][0]
        	#return d.fiscal_year
        	d.save()
        	webnotes.conn.commit()
		#return sender_no[1:-1]
		p=send_sms(message[1:-1],sender_no[1:-1])

        	return d.name   
		#else:
		#d= Document('Customer')
	        #d.customer_name=customer[1:-1]
                #d.customer_group='Individual'
		#d.customer_name=customer[1:-1]
        	#d.territory='India'
	        #d.save()
	        #webnotes.conn.commit()
        	#c= Document('Installation Note')
		#c.inst_time=time.strftime("%H:%M:%S")
                #c.inst_date=today
        	#c.customer=customer[1:-1]
		#c.customer_name=customer[1:-1]
		#c.complaint=complaint[1:-1]
		#c.status='Open'
                #c.complaint_date=today
        	#c.fiscal_year=res1[0][0]
        	#c.company='medsynaptic'
        	#c.territory='India' 
		#c.complaint_raised_by=customer[1:-1] 
        	#c.save()
        	#webnotes.conn.commit()
        	#return c.name

@webnotes.whitelist(allow_guest=True)
def get_support_ticket(code,sender_no,message,_type='POST'):
	#return "hello"
	from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
	today = nowdate()
        from webnotes.model.doc import Document
	import time
	#return sender_no[-11:]
	if code[1:-1] =="CRT":
		#return "hello"
		#return sender_no[1:-1]
		msg="Dear Customer,According to your request ticket is created"
	        d= Document('Support Ticket')
		d.opening_time=time.strftime("%H:%M:%S")
		d.opening_date=today
        	d.subject=message[1:-1]
        	d.raised_by=sender_no[1:-1]
		d.company='medsynaptic'
		d.status='Open'
        	d.save()
        	webnotes.conn.commit()
		#p=send_sms(message[1:-1],sender_no1[1:-1])
        	return d.name

	elif code[1:-1]=="CLS":
		#return "hii"
		#msg="Ticket Closed"
		#sender_no1=sender_no[-11:]
		z="select name from `tabSupport Ticket` where raised_by="+sender_no[1:-1]+" and status='Open'"
		x=webnotes.conn.sql(z)
		#return x 
		msg="Dear Customer,according to your request respective ticket is closed"
		if x:

			g="update `tabSupport Ticket` set status='Closed' where name='%s'"%(x[0][0])
			h=webnotes.conn.sql(g)
			#e=send_sms(message[1:-1],sender_no1[1:-1])
			return "Updated" 
			 

		else:
			pass

	else:
		pass


@webnotes.whitelist(allow_guest=True)
def get_activity_data(code,emp_id,client_name,place,deal_amount,product_sold=None,barcode=None,IR_NO=None,phone_no=None,payment_type=None,payment_mode=None,cheque_no=None,bank=None,cheque_status=None,service_call_type=None):
	
	from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
        today = nowdate()
        from webnotes.model.doc import Document
        import time
	#return code
	if (code[1:-1] =="SLD" or code =="SLO") and product_sold :

		d=Document('Activity Data')
		d.activity_id=d.name				
		d.activity_type=code[1:-1]
		d.emp_id=emp_id[1:-1]
		d.client_name=client_name[1:-1]
		d.place=place[1:-1]
		d.activity_date=today
		d.product_name=product_sold[1:-1]
		d.activity_time=time.strftime("%H:%M:%S")
		d.amount=deal_amount[1:-1]
		d.save()
                webnotes.conn.commit()
		return d.name
	elif (code[1:-1] =="INND" or code[1:-1] =="INNO" or code[1:1] =="INU") and barcode and IR_NO :
		#return barcode		
		d=Document('Activity Data')
               	d.activity_id=d.name
                d.activity_type=code[1:-1]
       	        d.emp_id=emp_id[1:-1]
               	d.client_name=client_name[1:-1]
                d.place=place[1:-1]
       	        d.activity_date=today
               	d.ir_no=IR_NO[1:-1]
		d.barcode=barcode[1:-1]
                d.activity_time=time.strftime("%H:%M:%S")
       	        d.amount=deal_amount[1:-1]
               	d.save()
                webnotes.conn.commit()
                return d.name

	elif (code[1:-1]=="AMCD" or code[1:-1]=="AMCO") and barcode:
		d=Document('Activity Data')
                d.activity_id=d.name
                d.activity_type=code[1:-1]
                d.emp_id=emp_id[1:-1]
                d.client_name=client_name[1:-1]
                d.place=place[1:-1]
                d.activity_date=today
                #d.ir_no=IR_NO[1:-1]
                d.barcode=barcode[1:-1]
                d.activity_time=time.strftime("%H:%M:%S")
                d.amount=deal_amount[1:-1]
                d.save()
                webnotes.conn.commit()
                return d.name

	elif (code[1:-1]=="SED" or code[1:-1]=="SEO") and service_call_type and barcode:
		d=Document('Activity Data')
                d.activity_id=d.name
                d.activity_type=code[1:-1]
                d.emp_id=emp_id[1:-1]
                d.client_name=client_name[1:-1]
                d.place=place[1:-1]
                d.activity_date=today
                  
		d.service_call_type=service_call_type[1:-1]
                d.barcode=barcode[1:-1]
                d.activity_time=time.strftime("%H:%M:%S")
                d.amount=deal_amount[1:-1]
                d.save()
                webnotes.conn.commit()
                return d.name
	elif code[1:-1]=="PR" and payment_type and payment_mode and cheque_no and bank and cheque_status and barcode:
		d=Document('Activity Data')
                d.activity_id=d.name
                d.activity_type=code[1:-1]
                d.emp_id=emp_id[1:-1]
               	d.client_name=client_name[1:-1]
                d.place=place[1:-1]
                d.activity_date=today
                #d.service_call_type=service_call_type[1:-1]
		d.payment_type=payment_type[1:-1]
		d.payment_mode=payment_mode[1:-1]
		d.cheque_no=cheque_no[1:-1]
		d.cheque_bank=bank[1:-1]
		d.cheque_status=cheque_status[1:-1]
                d.barcode=barcode[1:-1]
                d.activity_time=time.strftime("%H:%M:%S")
                d.amount=deal_amount[1:-1]
                d.save()
                webnotes.conn.commit()
                return d.name
	elif (code[1:-1]=="DC") and phone_no and product_sold:
		#return phone_no[-11:]
	 	d=Document('Activity Data')
                d.activity_id=d.name
                d.activity_type=code[1:-1]
               	d.emp_id=emp_id[1:-1]
                d.client_name=client_name[1:-1]
                d.place=place[1:-1]
                d.activity_date=today
                #d.service_call_type=service_call_type[1:-1]
               	d.product_name=product_sold[1:-1]
                d.activity_time=time.strftime("%H:%M:%S")
                d.amount=deal_amount[1:-1]
		c=phone_no[-11:]
		d.phone_no=c[1:-1]
                d.save()
                webnotes.conn.commit()
                return d.name
	else:
		"Last"


def get_escalation_for_supportticket():

	       #webnotes.errprint("in update")
               from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
               #from datetime import datetime
               #now = datetime.datetime.now().strftime("%Y-%m-%d")
               #webnotes.errprint(now)
               #yesterday = now - datetime.timedelta(days=1)
               #earlier = today - DD
               #earlier_str = earlier.strftime("%Y%m%d")
               #webnotes.errprint(now)
               #webnotes.errprint(yesterday)
               #webnotes.errprint(earlier)
               #webnotes.errprint(earlier_str)
               
               #today=nowdate()
               #i = datetime.now()
               #webnotes.errprint(i)
               #p=i.strftime('%Y-%m-%d %H:%M:%S')
               #webnotes.errprint(p)
               #day=p-timedelta(hours=24)
               #webnotes.errprint(day)
               qry=webnotes.conn.sql("select name from `tabSupport Ticket` t where t.status='Open' and t.creation < DATE_SUB(NOW(), INTERVAL 24 HOUR) AND          t.creation > DATE_SUB(NOW(), INTERVAL 48 HOUR)",as_list=1);

               webnotes.errprint(qry)
               if qry:
                       for [i] in qry:
                               webnotes.errprint(i)
                               p=webnotes.conn.sql("select territory from `tabSupport Ticket` where name='"+i+"'")
                               webnotes.errprint(p)
                               w=webnotes.conn.sql("select parent from `tabDefaultValue` where  defkey = '%s' and defvalue = '%s'"%('territory',p[0][0]))
                               webnotes.errprint(w)
                               webnotes.conn.sql("update `tabSupport Ticket` set assigned_to=' ',assigned_to_higher_level='"+w[0][0]+"' where name='"+i+"'")
                               webnotes.errprint("Updated")
               qr=webnotes.conn.sql("select name from `tabSupport Ticket` t where t.status='Open' and  t.creation < DATE_SUB(NOW(), INTERVAL 48 HOUR) AND creation > DATE_SUB(NOW(), INTERVAL 72 HOUR)",as_list=1);

               webnotes.errprint(qr)
               if qr:
                       for [j] in qr:
                               webnotes.errprint(j)
                               q=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='National Manager' and r.parent=p.name")
                               qt=webnotes.conn.sql("update `tabSupport Ticket` set assigned_to_higher_level='%s' where name='%s'"%(q[0][0],j))
                               webnotes.errprint(q)

               q=webnotes.conn.sql("select name from `tabSupport Ticket` t where t.status='Open' and t.creation < DATE_SUB(NOW(), INTERVAL 72 HOUR)",as_list=1);
               webnotes.errprint(q)
               if q:
                       for [k] in q:
                               webnotes.errprint(k)
                               q=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='COO' and r.parent=p.name")
                               qd=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='CEO' and r.parent=p.name")

                               qt=webnotes.conn.sql("update `tabSupport Ticket` set assigned_to='"+q[0][0]+"',assigned_to_higher_level=        '"+qd[0][0]+"' where name='"+k+"'")
                               webnotes.errprint("Updated")

def get_payment_followup():
#	 	from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
#         	from import datetime,date,timedelta
                i = datetime.now()
                p=i.strftime('%Y-%m-%d')
#
#
                webnotes.errprint(p)
                qry=webnotes.conn.sql("select name from `tabSales Invoice` where outstanding_amount>0",as_list=1)
                webnotes.errprint(qry)
#                #x=webnotes.conn.sql("select grand_total_export from `tabSales Invoice` where outstanding_amount>0",as_list=1)
#                #wevbnotes.conn.sql(x)
#
                for [i] in qry:
                        qr=webnotes.conn.sql("select installation from `tabSales Invoice` where name='"+i+"'",as_list=1)
                        webnotes.errprint(qr)
                        if qr:

                                q=webnotes.conn.sql("select inst_date,employee_id  from `tabInstallation Note` where name='"+qr[0][0]+"'")
                                #webnotes.errprint([q,"qqqq"])
                                webnotes.errprint(q[0][1])

                                y=webnotes.conn.sql("select grand_total_export from `tabSales Invoice` where name='"+qry[0][0]+"'",as_list=1)
                                webnotes.errprint(y)
                                v=webnotes.conn.sql("select outstanding_amount from `tabSales Invoice` where name='"+qry[0][0]+"'",as_list=1)
                                webnotes.errprint(v)
                                paid=flt(y[0][0]-v[0][0])
                                webnotes.errprint(paid)
                                if q:

                                        webnotes.errprint(q)
                                        s=q[0][0].strftime('%Y-%m-%d')
                                        a=getdate(p)
                                        e=cint((getdate(p) - getdate(s)).days)
                                        webnotes.errprint(e)
		                if e== 8:
                                        webnotes.errprint("in e")
                                        z=webnotes.conn.sql("select cell_number,user_id from `tabEmployee` where name='"+q[0][1]+"'")
                                        webnotes.errprint(z)
                                        ss=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='Manager' and r.parent=p.name")
                                        webnotes.errprint(ss)
                                        if ss:

                                                qq=webnotes.conn.sql("select cell_number from `tabEmployee` where user_id='"+ss[0][0]+"' and designation='Manager'")
                                                webnotes.errprint(qq)
                                        dic1={
                                                'Sales Invoice No':qry[0][0],
                                                'Installation Date':s,
                                                'Grand Total':y[0][0],
                                                'Outstanding Amount':v[0][0],
                                                'Paid Amount Till date': paid
                                        }
                                       #webnotes.errprint(flt(y[0][0]))
                                        msg="Dear Sir,sales Invoice No= '"+qry[0][0]+"' ,Installation Date='"+s+"',Total Amount for specified Sales Invoice is='"+cstr(y[0][0])+"', And Outstanding Amount='"+cstr(v[0][0])+"',And Paid Amount Till Date='"+cstr(paid)+"' "
                                        webnotes.errprint(msg)
                                        p=self.send_sms(z[0][0],msg)
                                        q=self.send_sms(qq[0][0],msg)
                                        r=self.send_email(z[0][1],msg)
                                        s=self.send_email(ss[0][0],msg)
                                        #x=self.send_email(z[0][1],msg)
                                        #webnotes.errprint(qry[0][0])

				elif e== 30:
                                        ss=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='National Manager' and r.parent=p.name")
                                        webnotes.errprint(ss)
                                        if ss:

                                                qq=webnotes.conn.sql("select cell_number from `tabEmployee` where user_id='"+ss[0][0]+"' and designation='National Manager'",as_list=1)
                                                #webnotes.errprint(qq)

                                        dic1={
			                        'Sales Invoice No':qry[0][0],
                        	                'Installation Date':s,
                            			'Grand Total':x[0][0],
                            			'Outstanding Amount':v[0][0],
                     			        'Paid Amount Till date':paid

                    }

                                        msg ="Dear Sir,sales Invoice No= '"+qry[0][0]+"' ,Installation Date='"+s+"', Total Amount for specified sales Invoice is='"+cstr(y[0][0])+"',And Outstanding Amount='"+cstr(v[0][0])+"',And Paid Amount Till Date='"+cstr(paid)+"' "
                                        p=send_sms(qq[0][0],msg)
					q=send_email(ss[0][0],msg)
				
			        elif e== 60:

                                        ss=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='CEO' and r.parent=p.name")
                                        webnotes.errprint(ss)
                                        if ss:

                                                qq=webnotes.conn.sql("select cell_number from `tabEmployee` where user_id='"+ss[0][0]+"' and designation='CEO'",as_list=1)
                                                webnotes.errprint(qq)

                                        ss1=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='COO' and r.parent=p.name")
                                        webnotes.errprint(ss1)
                                        if ss1:

                                                qq1=webnotes.conn.sql("select cell_number from `tabEmployee` where user_id='"+ss[0][0]+"' and designation='COO'",as_list=1)
                                                webnotes.errprint(qq1)

                                        dic1={
                                                'Sales Invoice No':qry[0][0],
                                                'Installation Date':s,
                                                'Grand Total':x[0][0],
                                                'Outstanding Amount':v[0][0],
                                                'Paid Amount Till date':paid

                    			}
                                        msg="Dear Sir,sales Invoice No= '"+qry[0][0]+"' ,Installation Date='"+s+"',Total Amount fro specified invoice is='"+cstr(y[0][0])+"',And Outstanding Amount='"+cstr(v[0][0])+"',And Paid Amount Till Date='"+cstr(paid)+"' "
                                       	p=send_sms(qq[0][0],msg)
                                        a=send_sms(qq1[0][0],msg)
					r=send_email(ss[0][0],msg)
					q=send_email(ss1[0][0],msg)

                                else:
                                        webnotes.errprint("in last")

			
