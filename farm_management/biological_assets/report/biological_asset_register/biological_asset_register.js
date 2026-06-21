frappe.query_reports["Biological Asset Register"] = {
	filters: [
		{
			fieldname: "farm",
			label: __("Farm"),
			fieldtype: "Link",
			options: "Farm"
		},
		{
			fieldname: "farm_type",
			label: __("Farm Type"),
			fieldtype: "Link",
			options: "Farm Type"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nHarvested\nSold\nDead Loss"
		}
	]
};
