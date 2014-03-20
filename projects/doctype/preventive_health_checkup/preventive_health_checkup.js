cur_frm.cscript.item= function(doc,cdt,cdn)
{
		//onsole.log("in employee");
		var d = locals[cdt][cdn];
		return get_server_fields('get_item', d.item, 'item_details_table', doc, cdt, cdn, 1);
}

cur_frm.cscript.employee= function(doc,cdt,cdn)
{
		//onsole.log("in employee");
		var d = locals[cdt][cdn];
		return get_server_fields('get_employee', d.employee, 'employee_details_table', doc, cdt, cdn, 1);
}