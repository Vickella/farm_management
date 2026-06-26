frappe.ui.form.on('Livestock Individual', {
    setup(frm) {
        frm.set_query('breed', () => ({
            filters: frm.doc.species ? {species: frm.doc.species} : {}
        }));
        frm.set_query('biological_asset', () => ({
            filters: frm.doc.farm ? {farm: frm.doc.farm, status: 'Active'} : {status: 'Active'}
        }));
    },
    species(frm) {
        frm.set_value('breed', null);
        frm.trigger('setup');
    },
    breed(frm) {
        if (!frm.doc.breed) {
            return;
        }
        frappe.db.get_value('Livestock Breed', frm.doc.breed, 'species').then((r) => {
            if (r.message && r.message.species) {
                frm.set_value('species', r.message.species);
            }
        });
    },
    farm(frm) {
        frm.trigger('setup');
    }
});