// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// show tasks
cur_frm.cscript.refresh = function(doc) {
	if(!doc.__islocal) {
		cur_frm.appframe.add_button(wn._("Gantt Chart"), function() {
			wn.route_options = {"project": doc.name}
			wn.set_route("Gantt", "Task");
		}, "icon-tasks");
		cur_frm.add_custom_button(wn._("Tasks"), function() {
			wn.route_options = {"project": doc.name}
			wn.set_route("List", "Task");
		}, "icon-list");
	}
}

cur_frm.fields_dict.customer.get_query = function(doc,cdt,cdn) {
	return{
		query:"controllers.queries.customer_query"
	}
}


cur_frm.cscript.project_category = function(doc,cdt,cdn){
                console.log("hhh")
                get_server_fields('get_milestone_details','','',doc,cdt,cdn,1,function(r,rt){refresh_field('project_milestones')});
 }

