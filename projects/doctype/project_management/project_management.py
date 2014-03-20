# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
from webnotes.model.doc import addchild
from webnotes.model.bean import getlist
from webnotes.model.doc import Document
from webnotes.utils import cint, cstr, flt, now, nowdate
import time 
import webnotes

class DocType:
	def __init__(self, d, dl):
		self.doc, self.doclist = d, dl

	def get_employee_details(self, employee):
		#webnotes.errprint("in details")
		#webnotes.errprint(["select employee_name,cell_number from `tabEmployee` where name=%s",employee])
		qry=webnotes.conn.sql("select employee_name,cell_number from `tabEmployee` where name=%s",employee,as_list=1)
		qr=webnotes.conn.sql("select cell_number from `tabEmployee` where name=%s",employee,as_list=1)
		return{
			'employee_name': qry[0][0],
			'employee_contact_no': qr[0][0]
		}
	def get_item(self, item):
		qry=webnotes.conn.sql("select description from `tabItem` where name=%s",item,as_list=1)
		q=webnotes.conn.sql("select default_warehouse from `tabItem` where name=%s",item,as_list=1)
		return{
			'description': qry[0][0],
			'warehouse': q[0][0]
		}

	#def get_patient(self,gender):
	#	webnotes.errprint(gender)
	#	if gender=='Female':
	#		return{
	#	
	#			'sugar_range':"70 - 140",
	#			'hb_range':"12.0-15.5",
	#			'blood_platlates_range':"150000 - 400000",
	#			'blood_pressure_range': "120 over 80"
	#		}
	#	else:
	#		 return{
	#	
        #                      'sugar_range':"70-110",
        #                      'hb_range': "13.5 to 17.5",
        #                      'blood_platlates_range':"150,000 - 400,000",
        #                       'blood_pressure_range':"117 over 77"
        #                }

	def get_item_details(self):
	
		items=webnotes.conn.sql(""" select item,quantity,description,warehouse from `tabItem Detail` 
					where parent=%s""",(self.doc.special_type_project),as_dict=1)
		employee=webnotes.conn.sql(""" select employee,employee_name,employee_contact_no from `tabEmployee Detail` 
					where parent=%s""",(self.doc.special_type_project),as_dict=1)
		#webnotes.errprint(milestone)
		for d in items:
			#self.doclist=self.doc.clear_table(self.doclist,'')

			ch = addchild(self.doc, 'item_details_table', 
					'Item Detail', self.doclist)
			#webnotes.errprint(t[0])
			ch.item = d.get('item')
			ch.quantity= d.get('quantity')
			ch.description=d.get('description')
			ch.warehouse=d.get('warehouse')
			#webnotes.errprint(ch)
		for t in employee:
			ch = addchild(self.doc, 'employee_details_table', 
				'Employee Detail', self.doclist)
				#webnotes.errprint(t[0])
			ch.employee=t.get('employee')
			ch.employee_name= t.get('employee_name')
			ch.employee_contact_no=t.get('employee_contact_no')
			#webnotes.errprint(ch)		

	def on_submit(self):
		#make_bin=[]	
		webnotes.errprint("in submit")
		self.set_actual_qty()
		self.get_patient_details()
		#from stock.stock_ledger import make_sl_entries
		#mandatory = ['posting_date','voucher_type','voucher_no','actual_qty','company']
		#for mn in mandatory:
		#	self.doc.fields[mn] = ''
		#make_sl_entries(make_bin)

	def set_actual_qty(self):
		from webnotes.utils import get_first_day, get_last_day, add_to_date, nowdate, getdate
        	today = nowdate()


		for p in getlist(self.doclist, 'item_details_table'):
			qr=webnotes.conn.sql(""" select is_asset_item from `tabItem` where item_code=%s""",p.item)
			if qr[0][0] =='No':
				#webnotes.errprint("Is not asset item")

				qry=webnotes.conn.sql("""select sum(actual_qty) from `tabStock Ledger Entry` where item_code=%s
					and warehouse=%s""",
					(p.item,p.warehouse))
				#webnotes.errprint(qry)
				qty_after_transaction=cstr(cint(qry[0][0])-cint(p.quantity))
				actual_qty=cstr(0-cint(p.quantity))
				tim=time.strftime("%X")
				#webnotes.errprint(qty_after_transaction)
	
				if cint(qty_after_transaction) < 0:
				
					webnotes.throw("Not enough quantity available at specified Warehouse for item=" +cstr(p.item))
				else:
					#webnotes.errprint("in stock ledger entry")							
					d = Document('Stock Ledger Entry')
					d.item_code=p.item
					#d.batch_no=p.batch_no
					d.actual_qty=actual_qty
					#webnotes.errprint(actual_qty)
					d.qty_after_transaction=qty_after_transaction
					#webnotes.errprint(d.qty_after_transaction)
					#d.stock_uom=p.product_uom
					d.warehouse=p.warehouse
					d.voucher_type='Project Management'
					#webnotes.errprint(d.voucher_type)
					#d.valuation_rate=p.product_rate
					#d.stock_value=p.quantity
					d.posting_date=today
					#webnotes.errprint(d.posting_date)
					#webnotes.errprint(d.posting_date)
					d.posting_time=tim
					#d.save()
					d.docstatus = 1;
					#d.name = 'SLE/00000008'
					d.owner = webnotes.session['user']
					d.fields['__islocal'] = 1
					d.voucher_no = self.doc.name
					d.voucher_detail_no =p.name
					d.save()
					a=webnotes.conn.sql("select actual_qty,projected_qty from`tabBin` where item_code='"+p.item+"'  and warehouse='"+p.warehouse+"'",as_list=1,debug=1)
					#webnotes.errprint(a)
					#webnotes.errprint(a[0][0])
					#webnotes.errprint(a[0][1])
					actual_qty=cstr(cint(a[0][0])-cint(p.quantity))
					projected_qty=cstr(cint(a[0][0])-cint(p.quantity))
					q=webnotes.conn.sql("update `tabBin` set actual_qty=%s,Projected_qty=%s where item_code='"+p.item+"' and warehouse='"+p.warehouse+"'",(actual_qty,projected_qty),debug=1)
					#webnotes.errprint("Updated")
					#make_bin.append({
					#	"doctype": 'pm',
					#	"sle_id":d.name,
					#	"item_code": p.item,
					#	"warehouse": p.warehouse,
					#	"actual_qty": cstr(0-cint(p.quantity))
					#	
					#})
			else:
				pass
	def get_patient_details(self):

		for f in getlist(self.doclist, 'patient_test_details'):
			if f.patient_id:

				d=Document('Patient Report')
				d.patient_id=f.patient_id
				d.patient_name=f.patient_name
				d.age=f.age
				d.gender=f.gender
				d.p_company=f.p_company
				d.company_address=f.company_address
				d.body_weight=f.body_weight
				d.bone_mineral_mass=f.bone_mineral_mass
				d.metabolic_age=f.metabolic_age
				d.whole_body_fat=f.whole_body_fat
				d.total_body_water=f.total_body_water
				d.height=f.height
				d.muscle_mass=f.muscle_mass
				d.visceral_fat=f.visceral_mass
				d.segment_body_fat=f.segment_body_fat
				d.body_weight_unit=f.body_weight_unit
				d.daily_calorie_intake=f.daily_calorie_intake
				d.sugar_level=f.sugar_level
				d.hb=f.hb
				d.height_unit=f.height_unit
				d.date_of_screening=f.date_of_screening				
				d.blood_group=f.blood_group
				d.body_mass_index=f.body_mass_index
				d.blood_pre=f.blood_pressure
				d.total_cholesterol=f.total_cholesterol
				d.ldl_cholesterol=f.ldl_cholesterol
				d.hdl_cholesterol=f.hdl_cholesterol
				d.serum_triglycerides=f.serum_triglycerides
				d.hba1c=f.hba1c
				d.cholesterol_ratio=f.cholesterol_ratio
				d.save()
			else:
				pass


