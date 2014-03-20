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
