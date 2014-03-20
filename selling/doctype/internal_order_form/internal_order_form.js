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



cur_frm.cscript.contact_mobile = function(doc){
	phone=doc.contact_mobile;
	phone = phone.replace(/[^0-9]/g, '');
	if(phone.length != 10) { 
   		alert("not 10 digits");
	} 
	//else {
  	//	alert("yep, its 10 digits");
	//}	 

}
