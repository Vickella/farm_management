frappe.query_reports["Animal Stock Ledger"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "farm",
			label: __("Farm"),
			fieldtype: "Link",
			options: "Farm"
		},
		{
			fieldname: "biological_asset",
			label: __("Biological Asset"),
			fieldtype: "Link",
			options: "Biological Asset"
		}
	]
};
