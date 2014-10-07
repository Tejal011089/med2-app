wn.query_reports["Target Setting and Monitoring"] = {
	"filters": [
		{
			"fieldname":"distribution",
			"label": "Distribution",
			"fieldtype": "Data",
			"width" : "80",
			//"options":"Querterly",
			"default": "Querterly"
		},
		{
                        "fieldname":"month",
                        "label": "Month",
                        "fieldtype": "Select",
                        "options":"\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12",
                        "width": "80",
                        //"default": wn.datetime.get_today()
                },


		{
			"fieldname":"from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"width": "80",
			//"default": sys_defaults.year_start_date,
		},
		{
			"fieldname":"to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"width": "80",
			//"default": wn.datetime.get_today()
		}


	]
}
