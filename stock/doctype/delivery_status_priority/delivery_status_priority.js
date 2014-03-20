

//cur_frm.cscript.status = function(doc,cdt,cdn)
//{
//		//console.log( "select priority from `tabStatus` where status='"+d.status+"' ")
//		console.log("in priority");
//		var d = locals[cdt][cdn];
//		return get_server_fields('get_delivery_details', d.status, 'delivery_tracking', doc, cdt, cdn, 1);
//		//console.log( "select priority from `tabStatus` where status='"+d.status+"' ")	
//}
cur_frm.cscript.refresh = function(doc,cdt,cdn){

	var cl = getchildren('Delivery Tracking', doc.name, 'delivery_tracking');


        //console.log(cl.length);

        //if(cl.length>5)
        //      msgprint("Sorry..!! Only Five Records can be added in insurance table");
        //else

        var arr= new Array();

       		for(i=0;i<cl.length;i++){


                        for(j=0;j<arr.length;j++){
                                //console.log(cl[i].priority == arr[j]);
                                if(cl[i].priority == arr[j]){
                                       //console.log("in if loop");
						
                                        msgprint("Duplicate Priority at Row Number "+(i+1)+" where status is '"+cl[i].status+"'");
                                	//throw("Duplicate Priority at Row Number "+(i+1)+" where status is '"+cl[i].status+"'");
				}
                                else
                                {
                                        //console.log("in else loop");

                                }
                   }
                arr.push(cl[i].priority);
                }
refresh_field('delivery_tracking');
}



cur_frm.cscript.custom_validate= function(doc, cdt, cdn) {
	ch=getchildren('Delivery Tracking',doc.name,'delivery_tracking');
	f=ch.length
	var arr1= new Array();
		 for(i=0;i<ch.length;i++){
			//console.log(ch[0].priority)
			if (ch[0].priority==1){
				//console.log("hieee");
				//arr1.push(ch[i].priority);
			 	//arr1.sort();
		
			}
			else
				msgprint("First Priority will be one alwayz");
		 		break;
	
	        }
		 for(j=0;j<ch.length;j++){	

			arr1.push(ch[j].priority)
			arr1.sort();
		 //console.log(arr1)
			
		 }	
		 //console.log(arr1)
		 //var mynumbers = new Array(1,2,3,6,9,10);
		 for(var i = 1; i < arr1.length; i++) {
    	 if(arr1[i] - arr1[i-1] != 1) {
        	msgprint("Priority must be sequential number. Here,missing number id: " + (arr1[i - 1] + 1));
        	break;
    	}
	}




}	
