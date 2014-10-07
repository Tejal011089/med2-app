// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.add_fetch('employee', 'company', 'company');

cur_frm.cscript.onload = function(doc, dt, dn){
  e_tbl = getchildren('Salary Structure Earning', doc.name, 'earning_details', doc.doctype);
  d_tbl = getchildren('Salary Structure Deduction', doc.name, 'deduction_details', doc.doctype);
  if (e_tbl.length == 0 && d_tbl.length == 0)
    return $c_obj(make_doclist(doc.doctype,doc.name),'make_earn_ded_table','', function(r, rt) { refresh_many(['earning_details', 'deduction_details']);});
}

cur_frm.cscript.refresh = function(doc, dt, dn){
  if((!doc.__islocal) && (doc.is_active == 'Yes')){
    cur_frm.add_custom_button(wn._('Make Salary Slip'), cur_frm.cscript['Make Salary Slip']);  
  }

  cur_frm.toggle_enable('employee', doc.__islocal);
}

cur_frm.cscript['Make Salary Slip'] = function() {
  console.log("in salary Structure")
	wn.model.open_mapped_doc({
		method: "hr.doctype.salary_structure.salary_structure.make_salary_slip",
		source_name: cur_frm.doc.name
	});
}

cur_frm.cscript.employee = function(doc, dt, dn){
  if (doc.employee)
    return get_server_fields('get_employee_details','','',doc,dt,dn);
}

cur_frm.cscript.modified_value = function(doc, cdt, cdn){
  calculate_totals(doc, cdt, cdn);
}

cur_frm.cscript.d_modified_amt = function(doc, cdt, cdn){
  calculate_totals(doc, cdt, cdn);
}

cur_frm.cscript.ctc = function(doc, cdt, cdn){
  //alert("hi");
  var d = locals[cdt][cdn];
  var pf =0;
  var gross=0;
  if (doc.ctc >= 13780) {
    pf = 780;
    gross=doc.ctc-780;
  }
  else{
    pf = (doc.ctc * 780) / 13780 ;
    gross=doc.ctc - pf;
  }

  
  var cl = getchildren('Salary Structure Earning', doc.name, 'earning_details', doc.doctype);
  for(var i = 0; i < cl.length; i++){
      if(cl[i].e_type=='Basic+D.A') cl[i].modified_value = gross/2;
      else if(cl[i].e_type=='H.R.A') cl[i].modified_value = (gross/2) * 0.40;
      else if(cl[i].e_type=='CONV') cl[i].modified_value = 800;
      else if(cl[i].e_type=='Fix Gross') cl[i].modified_value = gross;
      else if(cl[i].e_type=='Med All') {
        if (gross >7000) cl[i].modified_value = 1250;
        else cl[i].modified_value = 0;
      }
      else if(cl[i].e_type=='Other Allowances') {
        if (gross >=7000){
          Other=gross-((gross/2)+((gross/2) * 0.40)+800+1250);
          cl[i].modified_value = Other;
        }
        else {
          Other=gross-((gross/2)+((gross/2) * 0.40) + 800);
          cl[i].modified_value = Other;
        }
        
      }
    // console.log(cl[i].e_type=='Basic+D.A' && cl[i].modified_value < 6500)
  //if (cl[i].e_type=='Basic+D.A' && cl[i].modified_value < 6500){
     // var aa = (cl[i].modified_value * 0.12);
      // console.log(aa)
 // }
    }  
  refresh_field('earning_details');


  var cll = getchildren('Salary Structure Deduction', doc.name, 'deduction_details', doc.doctype);
  for(var i = 0; i < cll.length; i++){
      if(cll[i].d_type=='PF') {
        if (doc.ctc >= 13780) {
          pf = 780;
          cll[i].d_modified_amt = pf;
        }
        else{
          pf = (doc.ctc * 780) / 13780 ;
          cll[i].d_modified_amt = pf;
        }
      }

      else if(cll[i].d_type=='P.TAX'){
          if (gross > 10000) cll[i].d_modified_amt = 200;
          else if (gross > 5000 && gross <= 10000) cll[i].d_modified_amt = 175;
          else cll[i].d_modified_amt = 0;
      }
    }
  
  refresh_field('deduction_details');
    
}

var calculate_totals = function(doc, cdt, cdn) {
  var tbl1 = getchildren('Salary Structure Earning', doc.name, 'earning_details', doc.doctype);
  var tbl2 = getchildren('Salary Structure Deduction', doc.name, 'deduction_details', doc.doctype);
  
  var total_earn = 0; var total_ded = 0;
  for(var i = 0; i < tbl1.length; i++){
    total_earn += flt(tbl1[i].modified_value);
  }
  for(var j = 0; j < tbl2.length; j++){
    total_ded += flt(tbl2[j].d_modified_amt);
  }
  doc.total_earning = total_earn;
  doc.total_deduction = total_ded;
  doc.net_pay = flt(total_earn) - flt(total_ded);
  refresh_many(['total_earning', 'total_deduction', 'net_pay']);
}

cur_frm.cscript.validate = function(doc, cdt, cdn) {
  calculate_totals(doc, cdt, cdn);
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
  // return{ query:"controllers.queries.employee_query" } 
}
