
cur_frm.cscript.employee= function(doc,cdt,cdn)
{
		console.log("in employee");
		var t  = locals[cdt][cdn];
		return get_server_fields('get_employee_details', t.employee, 'employee_details_table', doc, cdt, cdn, 1);
}

cur_frm.cscript.item= function(doc,cdt,cdn)
{
		//onsole.log("in employee");
		var d = locals[cdt][cdn];
		return get_server_fields('get_item', d.item, 'item_details_table', doc, cdt, cdn, 1);
}
cur_frm.cscript.special_type_project= function(doc,cdt,cdn){
                //console.log("hhh")
        get_server_fields('get_item_details','','',doc,cdt,cdn,1,function(r,rt){refresh_field('item_details_table')},function(r,rt){refresh_field('employee_details_table')});
		//refresh_field('item_details_table');
		//refresh_field('employee_details_table');
}

cur_frm.cscript.refresh=function(doc,cdt,cdn){
	console.log("refresh");


}	


cur_frm.cscript.contact_no = function(doc){
        phone=doc.contact_no;
        phone = phone.replace(/[^0-9]/g, '');
        if(phone.length != 10)0
	{
               alert("Not 10 digits");
        } 
	//else {
        //        alert("yep, its 10 digits");
        // }

}
                      
//cur_frm.cscript.gender= function(doc,cdt,cdn)
//{
//                //onsole.log("in employee");
//                var d = locals[cdt][cdn];
//                return get_server_fields('get_patient', d.gender, 'patient_test_details', doc, cdt, cdn, 1);
//}

