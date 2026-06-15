import frappe
from frappe.model.document import Document
from frappe.utils import add_days, flt, today


class BiologicalAsset(Document):
    def validate(self):
        self.calculate_net_fair_value()
        self.validate_quantity()

    def calculate_net_fair_value(self):
        if self.current_fair_value is not None and self.cost_to_sell is not None:
            self.net_fair_value = flt(self.current_fair_value) - flt(self.cost_to_sell)
            self.accumulated_gain_loss = flt(self.net_fair_value) - flt(
                self.initial_cost
            )

    def validate_quantity(self):
        if flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")
        if self.mortality_to_date and flt(self.mortality_to_date) > flt(self.quantity):
            frappe.throw("Mortality cannot exceed total quantity.")

    def on_update(self):
        if not self.last_valuation_date:
            self.db_set("last_valuation_date", today(), update_modified=False)

    def post_fair_value_journal(self):
        if not self.accumulated_gain_loss:
            return None
        company = frappe.defaults.get_user_default(
            "Company"
        ) or frappe.db.get_single_value("Global Defaults", "default_company")
        je = frappe.new_doc("Journal Entry")
        je.posting_date = today()
        je.company = company
        je.voucher_type = "Journal Entry"
        je.remark = f"IFRS 41 Fair Value Adjustment — {self.asset_name}"
        gain_loss = flt(self.accumulated_gain_loss)
        je.append(
            "accounts",
            {
                "account": self.get_biological_asset_account(),
                "debit_in_account_currency": gain_loss if gain_loss > 0 else 0,
                "credit_in_account_currency": abs(gain_loss) if gain_loss < 0 else 0,
            },
        )
        je.append(
            "accounts",
            {
                "account": self.get_fair_value_gain_loss_account(),
                "credit_in_account_currency": gain_loss if gain_loss > 0 else 0,
                "debit_in_account_currency": abs(gain_loss) if gain_loss < 0 else 0,
            },
        )
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.msgprint(f"Journal Entry {je.name} posted for IFRS 41 adjustment.")
        return je

    def get_biological_asset_account(self):
        return frappe.db.get_single_value(
            "Farm Management Settings", "biological_asset_account"
        )

    def get_fair_value_gain_loss_account(self):
        return frappe.db.get_single_value(
            "Farm Management Settings", "fair_value_gain_loss_account"
        )


def update_fair_values():
    if not frappe.db.get_single_value(
        "Farm Management Settings", "enable_fair_value_scheduler"
    ):
        return
    cutoff = add_days(today(), -30)
    overdue = frappe.get_all(
        "Biological Asset",
        filters={"status": "Active", "last_valuation_date": ["<", cutoff]},
        fields=["name", "farm", "asset_name"],
    )
    for asset in overdue:
        _create_valuation_todo(asset)


def _create_valuation_todo(asset):
    if not frappe.db.exists(
        "ToDo",
        {
            "reference_type": "Biological Asset",
            "reference_name": asset.name,
            "status": "Open",
        },
    ):
        frappe.get_doc(
            {
                "doctype": "ToDo",
                "reference_type": "Biological Asset",
                "reference_name": asset.name,
                "description": f"Review fair value for {asset.asset_name}",
            }
        ).insert(ignore_permissions=True)
