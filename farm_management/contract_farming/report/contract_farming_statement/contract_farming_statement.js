frappe.query_reports["Contract Farming Statement"] = {
	filters: [
		{
			fieldname: "farm",
			label: __("Farm"),
			fieldtype: "Link",
			options: "Farm"
		},
		{
			fieldname: "farmer",
			label: __("Farmer"),
			fieldtype: "Link",
			options: "Outgrower Farmer"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nActive\nCompleted\nCancelled"
		}
	]
};
