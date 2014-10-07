// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
// License: GNU General Public License v3. See license.txt

wn.query_reports["Employee Wise Sales Order Report"] = {
        "filters": [
                {
                        "fieldname":"territory",
                        "label": "Region",
                        "fieldtype": "Link",
                        "options": "Territory",
                        //"default": wn.defaults.get_user_default("raw_item")
                },
                {
                        "fieldname":"owner",
                        "label": "Employee",
                        "fieldtype": "Link",
                        "options": "Profile",
                        //"default": wn.defaults.get_user_default("rawitem_warehouse")
                },
		{
                        "fieldname":"transaction date",
                        "label": " From Date",
                        "fieldtype": "Date",
                        //"options": "Item",
                        //"default": wn.defaults.get_user_default("product_code")
                },
                {
                        "fieldname":"creatoin",
                        "label": "To Date",
                        "fieldtype": "Date",
                        //"options": "Batch",
                        //"default": wn.defaults.get_user_default("select_batchno")
                },
                {
                        "fieldname":"customer_type",
                        "label": "OEM",
                        "fieldtype": "Select",
                        "options": ["","OEM","Direct"],
                        //"default": wn.defaults.get_user_default("select_batchno")
                },
                {
                        "fieldname":"item_code",
                        "label": "Product",
                        "fieldtype": "Link",
                        "options": "Item",
                        //"default": wn.defaults.get_user_default("select_batchno")
                },
		{
                        "fieldname":"net_total_export",
                        "label": "Amount",
                        "fieldtype": "Currency",
                        //"options": "Batch",
                        //"default": wn.defaults.get_user_default("select_batchno")
                },
                {
                        "fieldname":"total_commission",
                        "label": "Sales_Commission",
                        "fieldtype": "Currency",
                        //"options": "Batch",
                        //"default": wn.defaults.get_user_default("select_batchno")
                },

        ]
}
