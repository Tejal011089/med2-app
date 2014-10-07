
cur_frm.add_fetch('employee_id', 'region', 'territory');

cur_frm.cscript.number_of_installments = function(doc, cdt, cdn) {
	if(doc.number_of_installments && doc.doi_start){ 
		//return get_server_fields('get_end_date', '', '', doc, cdt, cdn, 1);
		//var myDate2 = new Date(doc.doi_start)
		//var result2 = myDate.addMonths(6)
		//console.log(result2)
		//console.log(mydate.addMonths(6));
		//var x = 12; //or whatever offset
		var CurrentDate = new Date(doc.doi_start);
		//console.log(CurrentDate.setMonth(CurrentDate.getMonth()+6));
		var d=new Date(CurrentDate.setMonth(CurrentDate.getMonth()+(doc.number_of_installments)));
		console.log(d)
		var p = d.getDate();
		var a = d.getMonth()+1;
		var b = d.getFullYear();
		var s = b +'-'+ a + '-' + p;
		console.log(s);
		doc.doi_closing=s;
		console.log(doc.doi_closing);
		t=flt(doc.loan_amount)/cint(doc.number_of_installments);
		console.log(t);
		doc.amount_per_month=t;
		refresh_field('amount_per_month')
		refresh_field('doi_closing');
		//return get_server_fields('get_end_date', '', '',s, doc, cdt, cdn, 1);
		//return doc.doi_closing;
	}
}	

cur_frm.cscript.doi_start = function(doc, cdt, cdn) {
	if(doc.number_of_installments && doc.doi_start){
		var CurrentDate = new Date(doc.doi_start);
		var d=new Date(CurrentDate.setMonth(CurrentDate.getMonth()+(doc.number_of_installments)));
		console.log(d)
		var p = d.getDate();
		var a = d.getMonth()+1;
		var b = d.getFullYear();
		var s = b +'-'+ a + '-' + p;
		console.log(s);
		doc.doi_closing=s;
		console.log(doc.doi_closing);
		t=flt(doc.loan_amount)/cint(doc.number_of_installments);
		console.log(t);
		doc.amount_per_month=t;
		refresh_field('amount_per_month')
		refresh_field('doi_closing');
	}
}	

//cur_frm.cscript.doi_start = function(doc, cdt, cdn) {
//	
//	get_server_fields('doi','','',doc, cdt, cdn, 1); 
	
//	refresh_field('doi_closing');
//};

// cur_frm.get_field("employee_id").get_query=function(doc,cdt,cdn)
// {
//    return "select name from `tabEmployee` where employee_name='"+user+"'"
// }

cur_frm.cscript.loan_str = function(doc,cdt,cdn){
	 	//console.log("hhh")
		get_server_fields('get_loan_details','','',doc,cdt,cdn,1,function(r,rt){refresh_field('installment')});
 }

// cur_frm.fields_dict.installment.grid.get_field("request_hr_not_to_deduct").get_query = function(doc,cdt,cdn)
// {	
//   var d = locals[cdt][cdn];
//   get_server_fields('get_deduction_details','',d.request_hr_not_to_deduct,doc,cdt,cdn,1,function(r,rt){refresh_field('installment')});
  
// }


cur_frm.cscript.request_hr_not_to_deduct = function(doc,cdt,cdn){
	 	var d = locals[cdt][cdn];
		var cl = getchildren('Loan Installment Details', doc.name, 'installment');
	 	var arr= new Array();
		args={}
		args = {
		maxdate: cl[cl.length-1].date_of_installment, 
		request: d.request_hr_not_to_deduct
	}
		
	 	//if(d.request_hr_not_to_deduct)
		return get_server_fields('get_deduction_details', JSON.stringify(args),'', doc, cdt, cdn, 1,function(r,rt){refresh_field('installment')});
 }

//cur_frm.cscript.amount_as_intrest = function(doc,cdt,cdn){
//             	console.log("intrest")
//		var amount=(((doc.loan_amount)+(doc.amount_as_intrest))/(doc.number_of_installments))
//                get_server_fields('get_amount_details','','',doc,cdt,cdn,1);
//		console.log(amount)
//		refresh_field('amount_per_month');
//}

