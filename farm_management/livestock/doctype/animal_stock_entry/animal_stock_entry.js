frappe.ui.form.on("Animal Stock Entry", {
	refresh(frm) {
		set_queries(frm);
		update_entry_type_fields(frm);
	},

	entry_type(frm) {
		update_entry_type_fields(frm);
	},

	quantity(frm) {
		update_amount(frm);
	},

	rate(frm) {
		update_amount(frm);
	},

	biological_asset(frm) {
		if (!frm.doc.biological_asset) {
			return;
		}

		frappe.db.get_value(
			"Biological Asset",
			frm.doc.biological_asset,
			["farm", "linked_project", "unit", "managed_item"]
		).then((r) => {
			const asset = r.message || {};
			frm.set_value("farm", asset.farm || frm.doc.farm);
			frm.set_value("project", asset.linked_project || frm.doc.project);
			frm.set_value("unit", asset.unit || frm.doc.unit);
		});
	},

	species(frm) {
		frm.set_value("breed", null);
		set_queries(frm);
	}
});

function set_queries(frm) {
	frm.set_query("breed", () => {
		return {
			filters: {
				species: frm.doc.species || ""
			}
		};
	});

	frm.set_query("biological_asset", () => {
		return {
			filters: {
				farm: frm.doc.farm || "",
				status: "Active"
			}
		};
	});
}

function update_amount(frm) {
	frm.set_value("amount", flt(frm.doc.quantity) * flt(frm.doc.rate));
}

function update_entry_type_fields(frm) {
	const decrease_types = ["Issue", "Sale", "Death", "Transfer Out", "Adjustment Decrease"];
	const cost_type = frm.doc.entry_type === "Cost Capitalization";
	const sale_type = frm.doc.entry_type === "Sale";
	const decrease_type = decrease_types.includes(frm.doc.entry_type);

	frm.toggle_display("item", cost_type);
	frm.toggle_display("sale_amount", sale_type);
	frm.toggle_display("sale_journal_entry", sale_type || frm.doc.sale_journal_entry);
	frm.toggle_display("asset_value_reduction", decrease_type || frm.doc.asset_value_reduction);
	frm.toggle_display("journal_entry", decrease_type || frm.doc.journal_entry);
	frm.toggle_display("capitalization", !decrease_type && (cost_type || frm.doc.capitalization));
	frm.toggle_reqd("rate", !decrease_type);
}
