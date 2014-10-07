// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

wn.provide("erpnext.hr");
erpnext.hr.EmployeeController = wn.ui.form.Controller.extend({
	setup: function() {
		this.frm.fields_dict.user_id.get_query = function(doc,cdt,cdn) {
				return { query:"core.doctype.profile.profile.profile_query"} }
		this.frm.fields_dict.reports_to.get_query = function(doc,cdt,cdn) {	
			return{	query:"controllers.queries.employee_query"}	}
	},
	
	onload: function() {
		this.setup_leave_approver_select();
		this.frm.toggle_display(["esic_card_no", "gratuity_lic_id", "pan_number", "pf_number"],
			wn.control_panel.country==="India");
		if(this.frm.doc.__islocal) this.frm.set_value("employee_name", "");
	},
	
	refresh: function() {
		var me = this;
		erpnext.hide_naming_series();
		if(!this.frm.doc.__islocal) {			
			cur_frm.add_custom_button(wn._('Make Salary Structure'), function() {
				me.make_salary_structure(this); });
		}
	},
	
	setup_leave_approver_select: function() {
		var me = this;
		return this.frm.call({
			method:"hr.utils.get_leave_approver_list",
			callback: function(r) {
				var df = wn.meta.get_docfield("Employee Leave Approver", "leave_approver",
					me.frm.doc.name);
				df.options = $.map(r.message, function(profile) { 
					return {value: profile, label: wn.user_info(profile).fullname}; 
				});
				me.frm.fields_dict.employee_leave_approvers.refresh();
			}
		});
	},
	
	date_of_birth: function() {
		return cur_frm.call({
			method: "get_retirement_date",
			args: {date_of_birth: this.frm.doc.date_of_birth}
		});
	},
	
	salutation: function() {
		if(this.frm.doc.salutation) {
			this.frm.set_value("gender", {
				"Mr": "Male",
				"Ms": "Female"
			}[this.frm.doc.salutation]);
		}
	},
	
	make_salary_structure: function(btn) {
		var me = this;
		this.validate_salary_structure(btn, function(r) {
			if(r.message) {
				msgprint(wn._("Employee") + ' "' + me.frm.doc.name + '": ' 
					+ wn._("An active Salary Structure already exists. \
						If you want to create new one, please ensure that no active \
						Salary Structure exists for this Employee. \
						Go to the active Salary Structure and set \"Is Active\" = \"No\""));
			} else if(!r.exc) {
				wn.model.map({
					source: wn.model.get_doclist(me.frm.doc.doctype, me.frm.doc.name),
					target: "Salary Structure"
				});
			}
		});
	},
	
	validate_salary_structure: function(btn, callback) {
		var me = this;
		return this.frm.call({
			btn: btn,
			method: "webnotes.client.get_value",
			args: {
				doctype: "Salary Structure",
				fieldname: "name",
				filters: {
					employee: me.frm.doc.name,
					is_active: "Yes",
					docstatus: ["!=", 2]
				},
			},
			callback: callback
		});
	},
});
cur_frm.cscript = new erpnext.hr.EmployeeController({frm: cur_frm});


cur_frm.cscript.cell_number = function(doc){
        phone=doc.cell_number;
        phone = phone.replace(/[^0-9]/g, '');
        if(phone.length != 10)
	{
               alert("not 10 digits");
        } 
	//else {
        //        alert("yep, its 10 digits");
        // }

}


cur_frm.cscript.status = function(doc){
	    if (doc.date_of_joining){
        var x=doc.date_of_joining;
        console.log(x);
        y=x.split('-');
        year=y[0];
        month=y[1];
        day=y[2];
        console.log(day);
        var d = new Date(year, month, day);
        if (doc.status=='Probation'){
        	d.setMonth(d.getMonth() + 6);
        	console.log(d);
            var combineDatestr = d.getDate() + "-" + d.getMonth() + "-" + d.getFullYear();
            console.log(combineDatestr);
            doc.evaluationprobation_end_date=combineDatestr;
            console.log(doc.evaluationprobation_end_date);
            refresh_field("evaluationprobation_end_date");
        }
        else if (doc.status=='Evaluation'){
	        d.setMonth(d.getMonth() + 3);
	        console.log(d);
	        var combineDatestr = d.getDate() + "-" + d.getMonth() + "-" + d.getFullYear();
	        console.log(combineDatestr);
	        doc.evaluationprobation_end_date=combineDatestr;
	        console.log(doc.evaluationprobation_end_date);
	        refresh_field("evaluationprobation_end_date");
        }

	else {
        	doc.evaluationprobation_end_date='';
	        console.log(doc.evaluationprobation_end_date);
	        refresh_field("evaluationprobation_end_date");
        }

    }
        
}


cur_frm.cscript.company_email = function(doc){

        var x=doc.company_email;
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
cur_frm.get_field("reporting_person").get_query=function(doc,cdt,cdn)
{
   return "Select p.name from `tabProfile` p, `tabUserRole` r where r.role='Leave Approver' and r.parent=p.name"
}
