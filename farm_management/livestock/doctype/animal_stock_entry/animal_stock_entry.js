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
			["farm", "linked_project", "unit", "managed_item", "net_fair_value", "quantity"]
		).then((r) => {
			const asset = r.message || {};
			frm.set_value("farm", asset.farm || frm.doc.farm);
			frm.set_value("project", asset.linked_project || frm.doc.project);
			frm.set_value("unit", asset.unit || frm.doc.unit);

			if (["Sale", "Issue", "Transfer"].includes(frm.doc.entry_type)) {
				if (asset.managed_item) {
					frappe.db.get_value("Livestock Species", {species_name: asset.managed_item}, "name").then((res) => {
						if (res && res.message && res.message.name) {
							frm.set_value("species", res.message.name);
						}
					});
				}
				if (asset.net_fair_value && asset.quantity) {
					frm.set_value("rate", flt(asset.net_fair_value) / flt(asset.quantity));
				}
			}
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
	const decrease_types = ["Issue", "Sale", "Death"];
	const sale_type = frm.doc.entry_type === "Sale";
	const decrease_type = decrease_types.includes(frm.doc.entry_type);

	frm.toggle_display("sale_amount", sale_type);
	frm.toggle_display("asset_value_reduction", decrease_type || frm.doc.asset_value_reduction);
	frm.toggle_reqd("rate", !decrease_type);
	
	const is_transfer = frm.doc.entry_type === "Transfer";
	frm.toggle_display("target_farm", is_transfer);
	frm.toggle_reqd("target_farm", is_transfer);
}
