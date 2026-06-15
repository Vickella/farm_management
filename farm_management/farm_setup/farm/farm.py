import json
import re

import frappe
from frappe.model.document import Document


class Farm(Document):
    def validate(self):
        self.validate_gps_format()
        self.validate_land_size()

    def validate_gps_format(self):
        if not self.gps_coordinates:
            return
        text = self.gps_coordinates
        try:
            data = json.loads(text) if isinstance(text, str) else text
            coords = (
                data.get("features", [{}])[0].get("geometry", {}).get("coordinates")
            )
            lon, lat = coords[:2]
        except Exception:
            match = re.search(r"(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)", str(text))
            if not match:
                frappe.throw(
                    "GPS Coordinates must contain latitude and longitude values."
                )
            lat, lon = float(match.group(1)), float(match.group(2))
        if not (-35 <= float(lat) <= -5 and 10 <= float(lon) <= 45):
            frappe.throw("GPS Coordinates must be plausible for Southern Africa.")

    def validate_land_size(self):
        if self.total_land_size is not None and self.total_land_size <= 0:
            frappe.throw("Total land size must be greater than zero.")

    def before_save(self):
        self.set_farm_manager_defaults()

    def set_farm_manager_defaults(self):
        if not self.operational_status:
            self.operational_status = "Active"
