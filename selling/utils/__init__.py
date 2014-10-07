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
               url = sms_url +"?username="+ args["username"] +"&password="+args["password"]+"&sendername="+ args["sendername"] +"&mobileno="+ sender_no +"&message=" + msg 
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
		#return d.employee_id
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
		m= None
		if not y :
		
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
	 	w="select y.parent from `tabDefaultValue` y,`tabProfile` p, `tabUserRole` r where  defkey = '%s' and defvalue = '%s' and r.role='Manager'"%('territory',r[0][0])
		a=webnotes.conn.sql(w)
		#return a
		from webnotes.model.doc import Document
		import time
	
    		#if res :
        	d = Document('Support Ticket')
		d.opening_time=time.strftime("%H:%M:%S")
		if y:
			d.raised_by=y[0][0]
		elif m:
			d.raised_by=z[0][0]
		else:
			d.raised_by=sender_no[-11:]
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
	#return sender_no[1:-1]
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
		p=send_sms(msg,sender_no[1:-1])
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
			webnotes.conn.sql("commit")
			e=send_sms(msg,sender_no[1:-1])
			#webnotes.er
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


@webnotes.whitelist(allow_guest=True)
def get_escalation_for_supportticket(_type='Post'):
	#print "get esc"
	#val = ''
        from webnotes.utils import cstr
        aa="select distinct(subdate(CURDATE(), 1)) from `tabHoliday` where subdate(CURDATE(), 1) not in (select holiday_date from `tabHoliday` where parent='2014-2015/Maharashtra/001')"
        res=webnotes.conn.sql(aa)
	s=Document('Support Ticket')
        j=0
        #print res
        if res:
               #print "in res "
               for i in range (2,15):
			#print "i"
			bb="select distinct(subdate(CURDATE(), "+cstr(i)+")) from `tabHoliday`"
                        #print bb
			res1=webnotes.conn.sql(bb)
			if res1:
			  cc="select distinct(subdate(CURDATE(), 1)) from `tabHoliday` where '"+cstr(res1[0][0])+"' in (select holiday_date from `tabHoliday` where parent='2014-2015/Maharashtra/001')"
			  #print cc
			  res2=webnotes.conn.sql(cc)
			  if res2:
			      #print "old j"
			      #print j
      			      j=j+24
		              #print "new j"
           		      #print j
			  else:
                             print "breaning "
			     break
	       
	       from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
	       qry1="select name from `tabSupport Ticket` t where t.status='Open' and t.creation < DATE_SUB(NOW(), INTERVAL 24+"+cstr(j)+" HOUR) AND  t.creation > DATE_SUB(NOW(), INTERVAL 48+"+cstr(j)+" HOUR)"
	       #print qry1	       
               qry=webnotes.conn.sql(qry1,as_list=1);
               webnotes.errprint("in 24 "+cstr(qry))
               if qry:
                       for [k] in qry:
 			       s=Document('Support Ticket')
                               webnotes.errprint(k)
                               p=webnotes.conn.sql("select territory from `tabSupport Ticket` where name='"+k+"'")
                               #webnotes.errprint(p)
                               w=webnotes.conn.sql("select y.parent from `tabDefaultValue` y,`tabProfile` p, `tabUserRole` r where  defkey = '%s' and defvalue = '%s' and r.role='Manager' and y.parent=p.name and r.parent=p.name"%('territory',p[0][0]))
                               #webnotes.errprint(w[0][0])
			       ee="update `tabSupport Ticket` set assigned_to='',assigned_to_higher_level='"+cstr(w[0][0])+"' where name='"+cstr(k)+"'"
			       #print ee
                               webnotes.conn.sql(ee)
			       webnotes.conn.commit()
			       #msg1 = ""
                               webnotes.errprint("Updated")
                               flg = webnotes.conn.sql("select flag from `tabSupport Ticket` where name ='"+cstr(k)+"'")
			       if flg[0][0]=="not":
				       em=w[0][0]
				       msg9="Support Ticket '"+k+"' assigned to you...Please check it."
	                       	       sendmail(em, subject='Support Ticket Alert', msg = msg9)
			       	       ss="update `tabSupport Ticket` set flag='fst' where name ='"+cstr(k)+"'"
				       webnotes.conn.sql(ss)
				       webnotes.conn.commit()
				
               qr=webnotes.conn.sql("select name from `tabSupport Ticket` t where t.status='Open' and  t.creation < DATE_SUB(NOW(), INTERVAL 48+"+cstr(j)+" HOUR) AND t.creation > DATE_SUB(NOW(), INTERVAL 72+"+cstr(j)+" HOUR)",as_list=1)
               webnotes.errprint("in 48 "+cstr(qr))
               if qr:
                       for [l] in qr:
                               webnotes.errprint(l)
                               q=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='National Manager' and r.parent=p.name")
	                       #print q
	                       ff="update `tabSupport Ticket` set assigned_to='',assigned_to_higher_level='"+cstr(q[0][0])+"' where name='"+cstr(l)+"'"
			       #print ff
                               webnotes.conn.sql(ff)
                               webnotes.conn.commit()
                               webnotes.errprint("Updated")
			       flg = webnotes.conn.sql("select flag from `tabSupport Ticket` where name ='"+cstr(l)+"'")
			       if flg[0][0]=="fst":
				       msg10="Support Ticket '"+l+"' assigned to you...Please check it."
                                       em=q[0][0]
				       sendmail(em, subject='Support Ticket Alert', msg = msg10)
			               ss="update `tabSupport Ticket` set flag='snd' where name ='"+cstr(l)+"'"
                                       webnotes.conn.sql(ss)
                                       webnotes.conn.commit()

               qs=webnotes.conn.sql("select name from `tabSupport Ticket` t where t.status='Open' and t.creation < DATE_SUB(NOW(), INTERVAL 72+"+cstr(j)+" HOUR) AND t.creation > DATE_SUB(NOW(), INTERVAL 100+"+cstr(j)+" HOUR)",as_list=1);
               webnotes.errprint("in 72 "+cstr(qs))
               if qs:
                       for [m] in qs:
			       s=Document('Support Ticket')
                               webnotes.errprint(m)
                               qa=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='COO' and r.parent=p.name")
                               qd=webnotes.conn.sql("Select p.name from `tabProfile` p, `tabUserRole` r where r.role='CEO' and r.parent=p.name")

                               qtt=webnotes.conn.sql("update `tabSupport Ticket` set assigned_to='"+qa[0][0]+"',assigned_to_higher_level=        '"+qd[0][0]+"' where name='"+m+"'")
			       webnotes.conn.commit()
                               webnotes.errprint("Updated")
			       flg = webnotes.conn.sql("select flag from `tabSupport Ticket` where name ='"+cstr(m)+"'")
			       if flg[0][0]=="snd":
				       msg11="Hello, Support Ticket '"+m+"' assigned to you...Please check it."
                                       em=qa[0][0]+","+qd[0][0]
				       sendmail(em, subject='Support Ticket Alert', msg = msg11)
			       	       ss="update `tabSupport Ticket` set flag='thrd' where name ='"+cstr(m)+"'"
                                       webnotes.conn.sql(ss)
				       webnotes.conn.commit()


@webnotes.whitelist(allow_guest=True)
def get_payment_followup():
	 	#from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
         	#from import datetime,date,timedelta
                i = datetime.now()
                p=i.strftime('%Y-%m-%d')
                webnotes.errprint(p)
                qry=webnotes.conn.sql("select name from `tabSales Invoice` where outstanding_amount>0",as_list=1)
                
                for [i] in qry:
                        qr=webnotes.conn.sql("select installation from `tabSales Invoice` where name='"+i+"'",as_list=1)
                        # webnotes.errprint(qr)
                        if qr:

                                q=webnotes.conn.sql("select inst_date,employee_id  from `tabInstallation Note` where name='"+qr[0][0]+"'")
                                #webnotes.errprint([q,"qqqq"])
                                # webnotes.errprint(q[0][1])

                                y=webnotes.conn.sql("select grand_total_export from `tabSales Invoice` where name='"+qry[0][0]+"'",as_list=1)
                                # webnotes.errprint(y)
                                v=webnotes.conn.sql("select outstanding_amount,customer from `tabSales Invoice` where name='"+qry[0][0]+"'",as_list=1)
                                # webnotes.errprint(v)
                                paid=flt(y[0][0]-v[0][0])
                                if v:
                                	customer_type=webnotes.conn.get_value('Customer',v[0][1],'customer_type')
                                	if customer_type=='OEM':
                                		credit_days=webnotes.conn.get_value('Customer',v[0][1],'credit_days')                  
                                	elif customer_type:
                                		credit_days=webnotes.conn.get_value('Global Defaults',None,'customer_credit_days')

                                if not credit_days:
                                	credit_days=0
                                	
                                #webnotes.errprint(["credit_days is here",credit_days])
                                if q:

                                        webnotes.errprint(q)
                                        s=q[0][0].strftime('%Y-%m-%d')
                                        a=getdate(p)
                                        e=cint((getdate(p) - getdate(s)).days)                                   
                                     
		                if e== cint(credit_days):
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

				elif e== 22+cint(credit_days):
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
				
			        elif e>= 52+cint(credit_days):

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


@webnotes.whitelist(allow_guest=True)
def fetch_sms(_type='POST'):
	aa="select id,creation,message_body,sender_no from smslog where flag=0 and sender_no is not null and message_body like '#%#'"
	bb=webnotes.conn.sql(aa)
	from webnotes.model.doc import Document
	import datetime,time
	from webnotes.utils import now,get_first_day, get_last_day, add_to_date, nowdate, getdate
	#print bb
	for r in bb:
		cc=r[2].split(',')
		dd=cc[0].upper().replace(' ','')
		#print cc
		#print len(cc)
		if dd=='#INNO' or dd=='#INND' or dd=='#INU':
			if len(cc)==7:
				#print "creation "+cstr( r)+"IN"
				d=Document('Activity Data')
                		#d.activity_id=d.name
                		d.activity_type=dd[1:]
                		d.emp_id=cc[2]
                		d.client_name=cc[4]
                		d.place=cc[5]
                		d.activity_date=now()
                		d.ir_no=cc[1]
                		d.barcode=cc[3]
				e=now().split(' ')
                		#d.activity_time=e[1]
                		d.amount=cc[6].replace('#','').replace(' ','')
				d.sender_phone_no=r[3]
                		d.save(new=1)
				webnotes.conn.commit()
				f=Document('Activity Data',d.name)
				f.activity_id=d.name
				f.save()
				if d.name:
					ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
					g=webnotes.conn.sql(ee)
					#print d.name
					webnotes.conn.commit()
		elif dd=='#CRT' or dd=='#CLS':
			from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
			today = nowdate()
			import time
			if dd=='#CRT' and len(cc)==3:
				print "crt "+cstr(r) +"CRT CLD"
				qr="select customer,employee_id from `tabInstallation Note` where product_barcode='"+cc[1]+"' "
				print qr
        			res=webnotes.conn.sql(qr)
				print res
				g=t=a=''
				if res:
					print "in if"
					gg="select name,customer_name,territory from tabCustomer where name='"+res[0][0]+"'"
					print gg
					g=webnotes.conn.sql(gg)
					print g
				        w="select status,user_id from `tabEmployee` where name='%s'"%(res[0][1]);
					print w
					t=webnotes.conn.sql(w)
					print t
					print "for employe"
					w="select y.parent from `tabDefaultValue` y,`tabProfile` p, `tabUserRole` r where  defkey = 'territory' and defvalue = '"+g[0][2]+"' and r.role='Manager' and y.parent=p.name and r.parent=p.name"
					print w
		                	a=webnotes.conn.sql(w)
					d=Document('Support Ticket')
					d.subject=cc[1]
					d.status='Open'
					#if res:
					if g:
						d.territory=g and g[0][2] or ''
						d.customer_name=g and g[0][1] or ''
						d.customer=g and g[0][0] or ''
					d.raised_by=r[3]
					d.opening_date=nowdate()
 					#e=now().split(' ')
					if t:
				    		if t[0][0] =='Left':
							d.assigned_to=a[0][0]
							d.assigned_to_higher_level=a[0][0]
							#return t[0][1]
				    		else:
			                    		d.assigned_to=t[0][1]
							d.assigned_to_higher_level=a[0][0]
					#e=now().split(' ')
					#d.sender_phone_no=r[3]
                        		#d.activity_time='01:01:01'
					d.save(new=1)
					webnotes.conn.commit()
					print d.name
					flg=webnotes.conn.sql("select flag from `tabSupport Ticket` where name = '"+d.name+"'")
					#print flg
					if flg[0][0]=="nott":
						msg8="Hello, Support Ticket '"+d.name+"' assigned to you...Please check it."
						print msg8
                                                em=t[0][1]+","+a[0][0]
						print em
                                                sendmail(em, subject='Support Ticket Alert', msg = msg8)
                                                ss="update `tabSupport Ticket` set flag='not' where name = '"+d.name+"'"
                                                webnotes.conn.sql(ss)
                                                webnotes.conn.commit()
	
					if d.name:
						p=Document('Communication')
                                                p.parent=d.name
                                                p.parentfield='Communications'
                                                p.parenttype='Support Ticket'
                                                p.content=cc[2].replace('#','')
						p.subject=cc[1]
						p.sender = d.raised_by
						p.save(new=1)
                               			ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
                                		g=webnotes.conn.sql(ee)
                                		webnotes.conn.commit()
			elif dd=='#CLS' and len(cc)==2:
			    if len(cc)==2:
				d=cc[1]
				#print d[:-1]
				#print "cls "+cstr(r)
				msgg="Dear Customer,according to your request respective ticket is closed."
				ee="update `tabSupport Ticket` set status='Closed' where name='"+cstr(d[:-1])+"'"
				print ee
				e="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
				print e
				print r
                                webnotes.conn.sql(ee)
				webnotes.conn.sql(e)
                                webnotes.conn.commit()
				no1=r[3]
				no = no1.replace("+", "")
				webnotes.errprint(no)
				print "END SMS..."
				pp=send_sms(msgg,no)
		elif dd=='#SLD' or dd=='#SLO':
				#print len(cc)
				if len(cc)==6 :
					print cc
					d=Document('Activity Data')
        	        		#d.activity_id=d.name
                			d.activity_type=dd[1:]
               	 			d.emp_id=cc[1]
                			d.client_name=cc[2]
              				d.place=cc[3]
					d.sender_phone_no=r[3]
                			d.activity_date=now()
               				d.product_name=cc[4]
                			#d.activity_time=time.strftime("%H:%M:%S")
               				d.amount=cc[5].replace('#','')
                			d.save(new=1)
                			webnotes.conn.commit()
					#print d.name
					f=Document('Activity Data',d.name)
        	                	f.activity_id=d.name
                	        	f.save()
	               			if d.name:
						ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
                                        	g=webnotes.conn.sql(ee)
                                        	webnotes.conn.commit()
		elif dd=='#AMCD' or dd=='#AMCO' :
		   if len(cc)==6:
	                d=Document('Activity Data')
        	        #d.activity_id=d.name
          	   	d.activity_type=dd[1:]
                	d.emp_id=cc[1]
                	d.client_name=cc[3]
                	d.place=cc[4]
                	d.activity_date=now()
                	#d.ir_no=IR_NO[1:-1]
                	d.barcode=cc[2]
                	#d.activity_time=time.strftime("%H:%M:%S")
                	d.amount=cc[5]
			d.sender_phone_no=r[3]
                	d.save(new=1)
                	webnotes.conn.commit()
			f=Document('Activity Data',d.name)
                        f.activity_id=d.name
                        f.save()
                	if d.name :
				ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
                                g=webnotes.conn.sql(ee)
                                webnotes.conn.commit()

	        elif dd=="#SED" or dd=="#SEO" :
		   if len(cc)==6 :
      	  	        d=Document('Activity Data')
        	        #d.activity_id=d.name
        	        d.activity_type=dd[1:]
  	    	        d.emp_id=cc[1]
	       	        d.client_name=cc[3]
        	        d.place=cc[4]
                	d.activity_date=now()
	                d.service_call_type=cc[5].replace('#','')
        	        d.barcode=cc[2]
			d.sender_phone_no=r[3]
                        d.save(new=1)
                        webnotes.conn.commit()
                        f=Document('Activity Data',d.name)
                        f.activity_id=d.name
                        f.save()
                        if d.name:
                                ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
                                g=webnotes.conn.sql(ee)
                                print d.name
                                webnotes.conn.commit()

	        elif dd=="#PR":
		   if len(cc)== 11:
	                d=Document('Activity Data')
        	        #d.activity_id=d.name
                	d.activity_type=dd[1:]
                	d.emp_id=cc[1]
                	d.client_name=cc[3]
                	d.place=cc[4]
                	d.activity_date=now()
                	#d.service_call_type=service_call_type[1:-1]
                	d.payment_type=cc[5]
                	d.payment_mode=cc[7]
                	d.cheque_no=cc[8]
                	d.cheque_bank=cc[9]
                	d.cheque_status=cc[10].replace('#','')
                	d.barcode=cc[2]
                	#d.activity_time=time.strftime("%H:%M:%S")
                	d.amount=cc[6]
			d.sender_phone_no=r[3]
                	d.save(new=1)
                	webnotes.conn.commit()
                        f=Document('Activity Data',d.name)
                        f.activity_id=d.name
                        f.save()
                        if d.name:
                                ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
                                g=webnotes.conn.sql(ee)
                                print d.name
                                webnotes.conn.commit()

	        elif dd=="#DC":
		  #print "creation for dc need 6 fields "+cstr(cc)
		  if len(cc)==6:
   	                #return phone_no[-11:]
        	        d=Document('Activity Data')
    	  	        #d.activity_id=d.name
        	        d.activity_type=dd[1:]
                	d.emp_id=cc[1]
                	d.client_name=cc[2]
                	d.place=cc[4]
                	d.activity_date=now()
			d.sender_phone_no=r[3]
                	#d.service_call_type=service_call_type[1:-1]
                	d.product_name=cc[5].replace('#','')
                	#d.activity_time=time.strftime("%H:%M:%S")
                	#d.amount=deal_amount[1:-1]
                	d.phone_no=cc[3]
                	d.save(new=1)
                	webnotes.conn.commit()
                        f=Document('Activity Data',d.name)
                        f.activity_id=d.name
                        f.save()
                        if d.name:
                                ee="update smslog set flag=1 where id='"+cstr(r[0])+"' and flag=0"
                                g=webnotes.conn.sql(ee)
                                print d.name
                                webnotes.conn.commit()

@webnotes.whitelist(allow_guest=True)
def posting():
	from werkzeug.wrappers import Request, Response
	return request.form['username']
	#return "hi"



@webnotes.whitelist(allow_guest=True)
def get_post(data,_type='POST'):
		from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
		from webnotes.model.doc import Document
		import time
		abc=json.loads(data)
		aa=Document('Installation Note')
		aa.customer=abc['customer_id']
		aa.customer_address=abc['address']
		aa.address_display=abc['address']
		aa.contact_person=abc['contact_person']
		aa.employee_id=abc['employee_no']
		aa.internal_order_no=abc['iof_no']
		aa.contact_email=abc['email']
		aa.contact_mobile=abc['phone']
		aa.clinic_name=abc['clinic_name']
		aa.doctor_name=abc['doctor_name']
		aa.city=abc['city']
		aa.pincode=abc['pincode']
		aa.director_name=abc['director_name']
		aa.state=abc['state']
		aa.reg_no_clinic=abc['reg_no_clinic']
		aa.reg_no_doctor=abc['reg_no_doctor']
		aa.website=abc['website']
		aa.palce=abc['palce']
		#aa.inst_date=abc['date_of_installation'].strftime('%Y-%m-%d')
		aa.employee_name=abc['employee_name']
		aa.inst_reprot_no=abc['inst_reprot_no']
		aa.user_name=abc['user_name']
		aa.dept=abc['dept']
		aa.contact_mobile=abc['contact_no']
		aa.dept1=abc['dept1']
		aa.contact_no1=abc['contact_no1']
		aa.product_barcode=abc['product_barcode']
		aa.version=abc['version']
		aa.material_supplied=abc['material_supplied']
		aa.inst_start_time=abc['inst_start_time']
		aa.inst_date=abc['inst_date']
		aa.inst_end_time=abc['inst_end_time']
		aa.inst_end_date=abc['inst_end_date']
		aa.proc=abc['proc']
		aa.ram=abc['ram']
		aa.hdd=abc['hdd']
		aa.me=abc['me']
		aa.other=abc['other']
		aa.model_no=abc['model_no']
		aa.serial_no=abc['serial_no']
		aa.os=abc['os']
		aa.inst_type=abc['inst_type']
		aa.no_in_case=abc['no_in_case']
		aa.training=abc['training']
		aa.customer_remark=abc['customer_remark']
		aa.engineers_remark=abc['engineers_remark']
		aa.status1=abc['status']
		aa.signature=abc['signature']
		aa.sign_seal=abc['sign_seal']
		aa.save(new=1)
		webnotes.conn.commit()
		return aa.name

@webnotes.whitelist(allow_guest=True)
def get_customer_detail(customer_id):
	qr="select customer_no,email from tabCustomer where name="+customer_id
	res=webnotes.conn.sql(qr)
	customerobj= {}
	for r in res:
		customerobj['phone'] = r[0]
		customerobj['email'] = r[1]
		customerobj['clinic_name'] = ''
		customerobj['address'] = ''
		customerobj['doctor_name'] = ''
		customerobj['city'] = ''
		customerobj['pincode'] = ''
		customerobj['director_name'] = ''
		customerobj['state'] = ''
		customerobj['email'] = ''
		customerobj['reg_no_clinic'] = ''
		customerobj['reg_no_doctor'] = ''
		customerobj['website'] = ''                    
    	return customerobj


@webnotes.whitelist(allow_guest=True)
def get_item_detail(barcode):
	qr="select name,item_code,description from `tabSerial No` limit 5"
	res=webnotes.conn.sql(qr)
	itemsobj= {}
	itemlist = []
	for r in res:
		itemobj={}
		itemobj['barcode'] = r[0]
		itemobj['description'] = r[1]                    
		itemobj['details'] = r[2]
		itemlist.append(itemobj)
    	return itemlist

@webnotes.whitelist(allow_guest=True)
def send_sales_details():
	print "sales details"
	from webnotes.utils.email_lib import sendmail
        qr="select a.territory,b.item_code,sum(b.qty) as qty,sum(b.export_amount) as amt from `tabSales Order Item` b,`tabSales Order` a  where a.name=b.parent group by b.item_code"
        res=webnotes.conn.sql(qr)
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Region</td><td>Product</td> <td>Quantity</td><td>Total Amount</td></tr>"""
	end="""</table></body></html>"""
	aa="""select distinct territory from `tabSales Order` where territory is not null order by territory"""
        res=webnotes.conn.sql(aa)
	msg=''
	for rr in res:
		msg1=''
        	bb="select ifnull(a.territory,''),ifnull(b.item_code,''),ifnull(sum(b.qty),''),ifnull(sum(b.export_amount),'') from `tabSales Order Item` b,`tabSales Order` a  where DATE(a.creation)=CURDATE() and a.name=b.parent and a.territory='"+rr[0]+"' group by b.item_code "
		#print bb
        	res1=webnotes.conn.sql(bb)
               	for rs in res1:
        	        #print rs
			#print msg
        	        msg=msg+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td></tr>"
			msg1=msg1+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td></tr>"
			#print msg
		msg2=start+""+cstr(msg1)+" "+end
		#print "------------------- region"
		#print msg2
		cc="SELECT p.name,y.defkey,y.defValue from `tabProfile` p, `tabUserRole` r, `tabDefaultValue` y where r.role='Regional Manager' and y.defkey='territory' and y.defvalue='"+rr[0]+"' and r.parent=p.name and p.name=y.parent"
		#print cc
		res3=webnotes.conn.sql(cc)
		for r in res3:
                   if res1:
		      	sendmail('gangadhar.k@indictranstech.com', subject='Regional Sales Alert', msg = msg2)
	msg3=start+""+cstr(msg)+" "+end
	if res1:
           sendmail('gangadhar.k@indictranstech.com', subject="sales alert", msg = msg3)
        return "done"


@webnotes.whitelist(allow_guest=True)
def send_ticket_details():
	print "ticket"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Region</td><td>Total Tickets Created</td> <td>Total Tickets Closed</td><td>Total Open Tickets</td><td>Total Paid Tickets</td><td>Total Paid Tickets Amount</td></tr>"""
	end="""</table></body></html>"""
	aa="""select distinct territory from `tabSupport Ticket` where territory is not null order by territory"""
        res=webnotes.conn.sql(aa)
	msg=''
	#print res
	for rr in res:
		msg1=''
        	bb="SELECT ifnull(a.territory,''),count(a.name),(select count(a.name) FROM `tabSupport Ticket` a WHERE DATE(a.creation)=CURDATE() and a.territory='"+cstr(rr[0])+"' and a.status='Closed' group by a.territory),(select count(a.name) FROM `tabSupport Ticket` a WHERE a.territory='"+cstr(rr[0])+"' and a.status<>'Closed' group by a.territory),(select count(a.name) FROM `tabSupport Ticket` a WHERE a.territory='"+cstr(rr[0])+"' and a.is_paid='Yes' group by a.territory),(select sum(amount) FROM `tabSupport Ticket` a WHERE a.territory='"+cstr(rr[0])+"' and a.is_paid='Yes' group by a.territory) FROM `tabSupport Ticket` a WHERE a.territory='"+cstr(rr[0])+"' group by a.territory "
		#print bb
        	res1=webnotes.conn.sql(bb)
               	for rs in res1:
        	        print rs
			#print msg
        	        msg=msg+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td><td>"+cstr(rs[5])+"</td></tr>"
			msg1=msg1+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td><td>"+cstr(rs[5])+"</td></tr>"
			#print msg
		msg2=start+""+cstr(msg1)+" "+end
		#print "------------------- region"
		#print msg2
		cc="SELECT p.name,y.defkey,y.defValue from `tabProfile` p, `tabUserRole` r, `tabDefaultValue` y where r.role='Regional Manager' and y.defkey='territory' and y.defvalue='"+rr[0]+"' and r.parent=p.name and p.name=y.parent"
		#print cc
		res3=webnotes.conn.sql(cc)
		for r in res3:
                   if res1:
		      	sendmail('gangadhar.k@indictranstech.com', subject='Regional Support Ticket Alert', msg = msg2)
	msg3=start+""+cstr(msg)+" "+end
	if res1:
           sendmail('gangadhar.k@indictranstech.com', subject="Support Ticket Alert", msg = msg3)
        return "done"


@webnotes.whitelist(allow_guest=True)
def send_isbpl_details():
	print "item sold below pricelist"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Region</td><td>Sales Order</td><td>Customer</td><td>Product</td><td>Price List Rate</td><td>Sold Rate</td></tr>"""
	end="""</table></body></html>"""
	aa="""select distinct territory from `tabSales Order` where territory is not null order by territory"""
        res=webnotes.conn.sql(aa)
	msg=''
	#print res
	for rr in res:
		msg1=''
        	bb="select a.territory,a.name,a.customer,b.item_code,b.ref_rate,b.export_rate from `tabSales Order Item` b,`tabSales Order` a  where DATE(a.creation)=CURDATE() and a.name=b.parent and b.ref_rate <> b.export_rate and b.ref_rate != 0 and a.territory='"+cstr(rr[0])+"' order by a.name "
		#print bb
        	res1=webnotes.conn.sql(bb)
               	for rs in res1:
        	        #print rs
			#print msg
        	        msg=msg+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td><td>"+cstr(rs[5])+"</td></tr>"
			msg1=msg1+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td><td>"+cstr(rs[5])+"</td></tr>"
			#print msg
		msg2=start+""+cstr(msg1)+" "+end
		print "------------------- region"
		print msg2
		cc="SELECT p.name,y.defkey,y.defValue from `tabProfile` p, `tabUserRole` r, `tabDefaultValue` y where r.role='Regional Manager' and y.defkey='territory' and y.defvalue='"+rr[0]+"' and r.parent=p.name and p.name=y.parent"
		#print cc
		res3=webnotes.conn.sql(cc)
		for r in res3:
			if res1:
				print "res in send mail"
		      		sendmail('gangadhar.k@indictranstech.com', subject='Regional Items Sold Below Price List Rate Alert', msg = msg2)
	msg3=start+""+cstr(msg)+" "+end
	print msg1
	if res1:	
           sendmail('gangadhar.k@indictranstech.com', subject="Items Sold Below Price List Rate Alert", msg = msg3)
        return "done"


@webnotes.whitelist(allow_guest=True)
def send_oppt_details():
	print "old oppts"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Region</td><td>Employee</td><td>Opportunity</td><td>LEAD/Customer</td><td>Created Before days</td></tr>"""
	end="""</table></body></html>"""
	aa="""select distinct territory from `tabOpportunity` where territory is not null order by territory"""
        res=webnotes.conn.sql(aa)
	msg=''
	#print res
	for rr in res:
		msg1=''
        	bb="select a.territory,a.owner,a.name,CASE a.enquiry_from  WHEN 'Customer' THEN a.customer ELSE a.lead END,DATEDIFF(CURDATE(),DATE(a.creation)) from `tabOpportunity` a where DATEDIFF(CURDATE(),DATE(a.creation))>=25 and status<> 'Quotation' and a.territory='"+rr[0]+"'order by a.owner,a.territory  "
		#print bb
        	res1=webnotes.conn.sql(bb)
               	for rs in res1:
        	        #print rs
			#print msg
        	        msg=msg+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td></tr>"
			msg1=msg1+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td></tr>"
			#print msg
		msg2=start+""+cstr(msg1)+" "+end
		print "------------------- region"
		print msg2
		cc="SELECT p.name,y.defkey,y.defValue from `tabProfile` p, `tabUserRole` r, `tabDefaultValue` y where r.role='Regional Manager' and y.defkey='territory' and y.defvalue='"+rr[0]+"' and r.parent=p.name and p.name=y.parent"
		#print cc
		res3=webnotes.conn.sql(cc)
		for r in res3:
			if res1:
				print "res in send mail"
		      		sendmail('gangadhar.k@indictranstech.com', subject='Regional Not Converted Opportunities Alert', msg = msg2)
	msg3=start+""+cstr(msg)+" "+end
	print msg1
	if res1:	
           sendmail('gangadhar.k@indictranstech.com', subject="Not Converted Opportunities Alert", msg = msg3)
        return "done"

@webnotes.whitelist(allow_guest=True)
def send_invoice_details():
	print "invoice not created"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Region</td><td>Employee</td><td>Sales Oder</td><td>Customer ID</td><td>Customer Name</td></tr>"""
	end="""</table></body></html>"""
	aa="""select distinct territory from `tabSales Order` where territory is not null order by territory"""
        res=webnotes.conn.sql(aa)
	msg=''
	#print res
	for rr in res:
		msg1=''
        	bb="select territory,owner,name,customer,customer_name from `tabSales Order` where territory='"+rr[0]+"' and name not in (select distinct(sales_order) from `tabSales Invoice Item` where sales_order is not null) order by territory,owner"
		#print bb
        	res1=webnotes.conn.sql(bb)
               	for rs in res1:
        	        #print rs
			#print msg
        	        msg=msg+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td></tr>"
			msg1=msg1+"<tr><td>"+cstr(rs[0])+"</td><td>"+cstr(rs[1])+"</td><td>"+cstr(rs[2])+"</td><td>"+cstr(rs[3])+"</td><td>"+cstr(rs[4])+"</td></tr>"
			#print msg
		msg2=start+""+cstr(msg1)+" "+end
		print "------------------- region"
		print msg2
		cc="SELECT p.name,y.defkey,y.defValue from `tabProfile` p, `tabUserRole` r, `tabDefaultValue` y where r.role='Regional Manager' and y.defkey='territory' and y.defvalue='"+rr[0]+"' and r.parent=p.name and p.name=y.parent"
		#print cc
		res3=webnotes.conn.sql(cc)
		for r in res3:
			if res1:
				print "res in send mail"
		      		sendmail('gangadhar.k@indictranstech.com', subject='Regional Invoices Not Created Alert', msg = msg2)
	msg3=start+""+cstr(msg)+" "+end
	print msg1	
        if res1:
           sendmail('gangadhar.k@indictranstech.com', subject="Invoices Not Created Alert", msg = msg3)
        return "done"

@webnotes.whitelist(allow_guest=True)
def send_amccmc_details():
	print "amc cmc"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >AMC/CMC Details</td><td>Asset Name </td><td>AMC/CMC Expiring Date</td></tr>"""
	end="""</table></body></html>"""
	aa="""select b.amc_details,a.item_code,datediff(date(b.expiry_date),CURDATE()), b.start_date,b.expiry_date  from `tabAMC Details` b,`tabItem` a where a.name=b.parent and expiry_date in(select max(expiry_date) from `tabAMC Details` where parent=b.parent) and datediff(date(b.expiry_date),CURDATE())<=15"""
        res=webnotes.conn.sql(aa)
	msg=''
	print res
	for rr in res:
		print rr
		print msg
        	msg=msg+"<tr><td>"+cstr(rr[0])+"</td><td>"+cstr(rr[1])+"</td><td>"+cstr(rr[4])+"</td></tr>"
		print msg
	msg1=start+""+cstr(msg)+" "+end
	print msg1
        if res:	
           sendmail('gangadhar.k@indictranstech.com', subject="AMC/CMC Expiring Alert", msg = msg1)
        return "done"

@webnotes.whitelist(allow_guest=True)
def send_todays_material_details():
	#print "todays_material_"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Purchase Order</td><td>Product </td><td>Quantity</td></tr>"""
	end="""</table></body></html>"""
	aa="""select a.name,b.item_code,b.schedule_date,b.qty from `tabPurchase Order`a,`tabPurchase Order Item`b where a.name not in(select d.prevdoc_docname from `tabPurchase Receipt`c,`tabPurchase Receipt Item`d where d.schedule_date=CURDATE() and d.parent=c.name) and b.schedule_date=CURDATE() and b.parent=a.name"""
        res=webnotes.conn.sql(aa)
	msg=''
	#print res
	for rr in res:
		#print rr
		#print msg
        	msg=msg+"<tr><td>"+cstr(rr[0])+"</td><td>"+cstr(rr[1])+"</td><td>"+cstr(rr[3])+"</td></tr>"
		#print msg
	msg1=start+""+cstr(msg)+" "+end
	if res:	
            sendmail('gangadhar.k@indictranstech.com', subject="Todays Expected Material Not Received Alert", msg = msg1)
        return "done"


@webnotes.whitelist(allow_guest=True)
def send_low_stock_details():
	print "low stock"
	from webnotes.utils.email_lib import sendmail
        start="""<html><head><style>table,th,td{border:1px solid black;border-collapse:collapse;}</style></head><table  style="width:100%";><tbody><tr style="background-color:Lime;color:white;"><td >Product</td><td>Warehouse </td><td>Actual Quantity in Warehouse</td><td>Minimum Quantity level</td></tr>"""
	end="""</table></body></html>"""
	aa="""select distinct a.item_code,a.warehouse,a.actual_qty,b.re_order_level from `tabBin`a,`tabItem`b where a.actual_qty<=b.re_order_level and b.re_order_level!=0"""
        res=webnotes.conn.sql(aa)
	msg=''
	#print res
	for rr in res:
		#print rr
		#print msg
        	msg=msg+"<tr><td>"+cstr(rr[0])+"</td><td>"+cstr(rr[1])+"</td><td>"+cstr(rr[2])+"</td><td>"+cstr(rr[3])+"</td></tr>"
		#print msg
	msg1=start+""+cstr(msg)+" "+end
	if res:	
       		 sendmail('gangadhar.k@indictranstech.com', subject="Minimum Stock Level Reached Alert", msg = msg1)
        return "done"



@webnotes.whitelist(allow_guest=True)
def GetVerify(verificationCode):
	return '0^232322422'

@webnotes.whitelist(allow_guest=True)
def GetEmployee(sessionCode,empID):
	aa="select employee_name from tabEmployee where name="+empID
	res=webnotes.conn.sql(aa)
	if res:
	    return '0^'+res[0][0]
	else:
		return "Employee not found for employee ID "+empID

@webnotes.whitelist(allow_guest=True)
def GetProducts(sessionCode,instType,customerID):
	if sessionCode:
	    return '0^53424423423'
	else:
		return "1^invalid session code"

@webnotes.whitelist(allow_guest=True)
def GetInstDetails(sessionCode,instType,prodBarCode):
	if sessionCode:
	    return '0^shree clinic^deccan pune^Dr.Metgud^pune^411004^Dr. Sanjay Joshi^Maharashtra^sanjayjoshi@gmail.com^9822012345^www.sanjayjoshi.com^MH/REG/CL/21232^MH/REG/DR/212323^IN00004^ScanDoc^IOF-00003^2242423~3423424545~553534434~353r445345~3434434'
	else:
		return "1^invalid session code"

@webnotes.whitelist(allow_guest=True)
def SetRegister(sessionCode,instType,customerID,prodBarCode,empID,prodName,prodVersion,iofNumber,instReportNumber,contactPersonsOnSite,mateBarCode):
	if sessionCode:
	    return '0^IN00004'
	else:
		return "1^invalid session code"
