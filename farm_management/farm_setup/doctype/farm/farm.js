frappe.ui.form.on("Farm", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__("View Weather Forecast"), () => {
			frappe.route_options = {farm: frm.doc.name};
			frappe.set_route("farm-weather");
		}, __("Farm Operations"));
	},
});
