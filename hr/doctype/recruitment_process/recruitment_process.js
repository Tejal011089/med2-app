cur_frm.cscript.email_id = function(doc){

        var x=doc.email_id;
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

cur_frm.cscript.alternate_emailid = function(doc){

        var x=doc.alternate_emailid;
        //console.log(x)
        var atpos=x.indexOf("@");
        var dotpos=x.lastIndexOf(".");
        if (atpos<1 || dotpos<atpos+2 || dotpos+2>=x.length)
        {
                alert("Not a valid e-mail address");
                return false;
        }
        else
                console.log("valid")
}


cur_frm.cscript.birth_date = function(doc){

	//console.log("in birth date");
	var first=doc.birth_date;
	//console.log(first);
	var currentTime = new Date()
	var month = currentTime.getMonth() + 1
	var day = currentTime.getDate()
	var year = currentTime.getFullYear()
	if (month!=10 && month!=11 && month!=12){

		second=year + "-"+"0" + month + "-" + day
		//console.log(second)
	}
	else
		second=year + "-" + month + "-" + day
	if (first>=second)
		alert("Please enter valid birth date")
}

cur_frm.cscript.phone_number = function(doc){
        phone=doc.phone_number;
        phone = phone.replace(/[^0-9]/g, '');
        if(phone.length != 10)
        {
               alert("not 10 digits");
	       return false;
        }  
        //else {
        //        alert("yep, its 10 digits");
        // }

}

//cur_frm.fields_dict.work_details.grid.get_field("contact").get_query = function(doc,cdt,cdn)
//{
//   console.log("contact")
//    var d = locals[cdt][cdn];
//    var t= d.contact
//    console.log(t)
//    t = t.replace(/[^0-9]/g, '');
//        if(t.length != 10)
//        {
//               alert("Not 10 digits");
//           return false;
//        }  

//}