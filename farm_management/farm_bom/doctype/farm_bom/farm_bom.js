frappe.ui.form.on("Farm BOM Item", {
	item: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item) {
			frappe.db.get_value("Item", row.item, "stock_uom", function(r) {
				if (r && r.stock_uom) {
					frappe.model.set_value(cdt, cdn, "unit", r.stock_uom);
				}
			});
		}
	},
	unit: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item && row.unit) {
			frappe.db.get_value("Item", row.item, "stock_uom", function(r) {
				if (r && r.stock_uom && r.stock_uom !== row.unit) {
					frappe.msgprint(__("Warning: Unit {0} does not match the default Stock UOM {1} for Item {2}", [row.unit, r.stock_uom, row.item]));
				}
			});
		}
	}
});
