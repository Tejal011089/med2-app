cur_frm.cscript.onload = function(doc, cdt, cdn) {
//console.log("hello gangadhar onload");
get_server_fields('get_dtl','','',doc,cdt,cdn,1,clbk);
//console.log("call clkkd");
}


var clbk=function(doc,cdt,cdn){
//console.log("resfresdf tbl");
refresh_field('edit_sms');
}
