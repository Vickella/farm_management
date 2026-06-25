frappe.ui.form.on("Farm BOM", {
	refresh: function(frm) {
		calculate_total_cost(frm);
	}
});

frappe.ui.form.on("Farm BOM Item", {
	item: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item) {
			frappe.db.get_value("Item", row.item, ["stock_uom", "valuation_rate"], function(r) {
				if (r) {
					let updates = {};
					if (r.stock_uom) updates.unit = r.stock_uom;
					if (r.valuation_rate) updates.unit_cost = r.valuation_rate;
					frappe.model.set_value(cdt, cdn, updates);
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
	},
	quantity: function(frm, cdt, cdn) {
		calculate_row_total(frm, cdt, cdn);
	},
	unit_cost: function(frm, cdt, cdn) {
		calculate_row_total(frm, cdt, cdn);
	},
	bom_items_remove: function(frm) {
		calculate_total_cost(frm);
	}
});

function calculate_row_total(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total = (row.quantity || 0) * (row.unit_cost || 0);
	frappe.model.set_value(cdt, cdn, "total_cost", total);
	calculate_total_cost(frm);
}

function calculate_total_cost(frm) {
	let total_cost = 0;
	if (frm.doc.bom_items) {
		frm.doc.bom_items.forEach(item => {
			total_cost += item.total_cost || 0;
		});
	}
	frm.set_value("total_estimated_cost", total_cost);
}
