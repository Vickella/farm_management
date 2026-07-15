"""Shared document lifecycle rules for Farm Management transaction DocTypes."""


def sync_status_on_submit(doc, method=None):
    _sync_status(doc, ("Submitted", "Completed", "Active", "Approved"))


def sync_status_on_cancel(doc, method=None):
    _sync_status(doc, ("Cancelled", "Canceled"))


def _sync_status(doc, preferred_statuses):
    if not doc.meta.is_submittable or not doc.meta.has_field("status"):
        return
    field = doc.meta.get_field("status")
    options = [option.strip() for option in (field.options or "").splitlines() if option.strip()]
    status = next((value for value in preferred_statuses if value in options), None)
    if status and doc.get("status") != status:
        doc.db_set("status", status, update_modified=False)
