import frappe


def apply_farm_permission_filter(
    conditions, values, sql_field="farm", requested_farm=None
):
    """Apply Frappe Farm read permissions to a direct-SQL report."""
    allowed_farms = frappe.get_list("Farm", pluck="name")
    if requested_farm:
        if requested_farm not in allowed_farms:
            return False
        conditions.append(f"{sql_field} = %(farm)s")
        values["farm"] = requested_farm
        return True
    if not allowed_farms:
        return False
    conditions.append(f"{sql_field} in %(allowed_farms)s")
    values["allowed_farms"] = tuple(allowed_farms)
    return True
