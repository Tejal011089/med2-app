cur_frm.cscript.email = function(doc){

        var x=doc.email;
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



cur_frm.cscript.phone_number = function(doc){
        phone=doc.phone_number;
        phone = phone.replace(/[^0-9]/g, '');
        if(phone.length != 10)0
	{
               alert("not 10 digits");
        } 
	//else {
        //        alert("yep, its 10 digits");
        // }

}
                            
