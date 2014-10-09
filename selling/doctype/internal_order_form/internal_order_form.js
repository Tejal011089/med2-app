// cur_frm.cscript.refresh=function(doc,cdt,cdn){
// 	if(doc.docstatus == 1 && doc.status =='Approved') {
// 			cur_frm.add_custom_button(wn._('Make Sales Order'), 
// 			cur_frm.cscript['Make Sales Order']);
// 	}
// }

// cur_frm.cscript['Make Sales Order'] = function() {
// 	wn.model.open_mapped_doc({
// 		method: "selling.doctype.internal_order_form.internal_order_form.make_sales_order",
// 		source_name: cur_frm.doc.name
// // 	})
// 	if(doc.docstatus==1) {
// 					if(flt(doc.per_delivered, 2) < 100 && doc.order_type=='Sales'){
// 						cur_frm.add_custom_button(wn._('Make Delivery'), this.make_delivery_note);
// 					}
// 					// maintenance
// 					if(flt(doc.per_delivered, 2) < 100 && (doc.order_type !='Sales')) {
// 						cur_frm.add_custom_button(wn._('Make Maint. Visit'), this.make_maintenance_visit);
// 						cur_frm.add_custom_button(wn._('Make Maint. Schedule'), 
// 							this.make_maintenance_schedule);
// 					}

// 					// indent
// 					if(!doc.order_type || (doc.order_type == 'Sales')){
// 						cur_frm.add_custom_button(wn._('Make ') + wn._('Material Request'), 
// 							this.make_material_request);
// 					}
// 					// sales invoice
// 					if(flt(doc.per_billed, 2) < 100)
// 						cur_frm.add_custom_button(wn._('Make Invoice'), this.make_sales_invoice);
//  	}

//  	else
//  			console.log("fff")
// },


// order_type: function() {
// 		this.frm.toggle_reqd("delivery_date", this.frm.doc.order_type == "Sales");
// 	},

// tc_name: function() {
// 		this.get_terms();
// },
	
// 	reserved_warehouse: function(doc, cdt, cdn) {
// 		var item = wn.model.get_doc(cdt, cdn);
// 		if(item.item_code && item.reserved_warehouse) {
// 			return this.frm.call({
// 				method: "selling.utils.get_available_qty",
// 				child: item,
// 				args: {
// 					item_code: item.item_code,
// 					warehouse: item.reserved_warehouse,
// 				},
// 			});
// 		}
// 	},

// 	make_material_request: function() {
// 		wn.model.open_mapped_doc({
// 			method: "selling.doctype.sales_order.sales_order.make_material_request",
// 			source_name: cur_frm.doc.name
// 		})
// 	},

// 	make_delivery_note: function() {
// 		wn.model.open_mapped_doc({
// 			method: "selling.doctype.sales_order.sales_order.make_delivery_note",
// 			source_name: cur_frm.doc.name
// 		})
// 	},

// 	make_sales_invoice: function() {
// 		wn.model.open_mapped_doc({
// 			method: "selling.doctype.sales_order.sales_order.make_sales_invoice",
// 			source_name: cur_frm.doc.name
// 		})
// 	},
	
// 	make_maintenance_schedule: function() {
// 		wn.model.open_mapped_doc({
// 			method: "selling.doctype.sales_order.sales_order.make_maintenance_schedule",
// 			source_name: cur_frm.doc.name
// 		})
// 	}, 
	
// 	make_maintenance_visit: function() {
// 		wn.model.open_mapped_doc({
// 			method: "selling.doctype.sales_order.sales_order.make_maintenance_visit",
// 			source_name: cur_frm.doc.name
// 		})
// 	},

//}	

//cur_frm.add_fetch('employee', 'region', 'territory');
cur_frm.cscript.tname = "'Internal Order Item Details'";
cur_frm.cscript.fname = "internal_order_item";

cur_frm.add_fetch("contact_person", "designation","contact_person_designation");

wn.require('app/selling/sales_common.js');

erpnext.selling.InternalOrderFormController = erpnext.selling.SellingController.extend({
  
  onload: function(doc, dt, dn) {
    this._super(doc, dt, dn);
    console.log("hi")
    // if(doc.customer && !doc.quotation_to)
    //   doc.quotation_to = "Customer";
    // else if(doc.lead && !doc.quotation_to)
    //   doc.quotation_to = "Lead";
  
  }

});

cur_frm.script_manager.make(erpnext.selling.InternalOrderFormController);

cur_frm.cscript.contact_email = function(doc){

	var x=doc.contact_email;
	//console.log(x)
	var atpos=x.indexOf("@");
	var dotpos=x.lastIndexOf(".");
	if (atpos<1 || dotpos<atpos+2 || dotpos+2>=x.length)
  	{
  		alert("Not a valid e-mail address");
  		return false;
  	}	
		//else
		//console.log("bbbb")
}


cur_frm.cscript.customer = function(doc, cdt, cdn) {
  if(doc.customer) 
   // console.log("in customer")
    return get_server_fields('get_cust_addr', '', '', doc, cdt, cdn, 1);

}

cur_frm.fields_dict.accessories_details.grid.get_field("item_code").get_query = function(doc){
        //console.log("hhhh");

        return "select name from `tabItem` where item_group='Products' and name like '%s'"
}

cur_frm.fields_dict.accessories_details.grid.get_field("item").get_query = function(doc){
        //console.log("hhhh");

        return "select name from `tabItem` where item_group='Accessories' and name like '%s'"
}


cur_frm.get_field("contact_person").get_query=function(doc,cdt,cdn)
{   
  if(doc.customer)
   return "select name from `tabContact` where customer='"+doc.customer+"'"
  else
    msgprint("Specify customer first");
}

cur_frm.cscript.add = function(doc,cdt,cdn){
                //console.log("hhh")
                var d = locals[cdt][cdn];
                //console.log(d.item)
                if(d.item){

                        //console.log("if loop")
                        //get_server_fields('get_accessories_details', d.item, 'accessories_details', doc, cdt, cdn, 1,function(r,rt){refresh_field('accessories_details')});
                        //return get_server_fields('get_accessories_details',d.item,'',doc,cdt,cdn,1,function(r,rt){refresh_field('accessories_details')});
                        get_server_fields('get_accessories_details',d.item,'',doc,cdt,cdn,1,function(r,rt){refresh_field('internal_order_item')});
                }
                else
                        alert("Accessories Field  can not be blank")
 }

cur_frm.cscript.contact_mobile = function(doc){
	phone=doc.contact_mobile;
	phone = phone.replace(/[^0-9]/g, '');
	if(phone.length != 10) { 
   		alert("Not 10 digits");
	} 
	//else {
  	//	alert("yep, its 10 digits");
	//}	 

}
cur_frm.cscript.referring_person = function(doc,cdt,cdn){
	console.log(doc.referring_person);
	if (doc.referring_person){
		get_server_fields('get_bank_details',doc.referring_person,'',doc,cdt,cdn,1);




	}		
}
