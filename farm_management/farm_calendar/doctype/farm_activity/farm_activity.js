frappe.ui.form.on('Farm Activity', {
    refresh: function(frm) {
        // Activity calculations
    },
    validate: function(frm) {
        // Assuming actual_cost and estimated_cost are calculated from linked timesheets or BOMs
        // Here is a basic script that could be expanded
        let estimated = 0;
        let actual = 0;
        
        // Placeholder for timesheet integration or inputs
        
        // frm.set_value('estimated_cost', estimated);
        // frm.set_value('actual_cost', actual);
    }
});
