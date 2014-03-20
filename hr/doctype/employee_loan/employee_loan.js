
cur_frm.cscript.number_of_installments = function(doc, cdt, cdn) {
	if(doc.number_of_installments) 
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

cur_frm.cscript.loan_str = function(doc,cdt,cdn){
	 	console.log("hhh")
		get_server_fields('get_loan_details','','',doc,cdt,cdn,1,function(r,rt){refresh_field('installment')});
 }


//cur_frm.cscript.amount_as_intrest = function(doc,cdt,cdn){
//             	console.log("intrest")
//		var amount=(((doc.loan_amount)+(doc.amount_as_intrest))/(doc.number_of_installments))
//                get_server_fields('get_amount_details','','',doc,cdt,cdn,1);
//		console.log(amount)
//		refresh_field('amount_per_month');
//}

