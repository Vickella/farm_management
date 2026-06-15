import frappe
from frappe import _


@frappe.whitelist()
def get_agri_response(question, context_farm=None):
    system_prompt = _build_system_prompt(context_farm)
    api_key = frappe.conf.get("openai_api_key") or frappe.db.get_single_value(
        "Farm Management Settings", "ai_api_key"
    )
    if not api_key:
        frappe.throw(
            _("AI API key not configured. Please set it in Farm Management Settings.")
        )
    response = _call_ai_api(system_prompt, question, api_key)
    return {"response": response, "question": question}


def _build_system_prompt(farm_name=None):
    base = (
        "You are AgriGPT, an expert agricultural advisor specialising in Southern African farming. "
        "You have deep knowledge of crop farming, livestock, poultry, aquaculture, IFRS 41 biological asset "
        "accounting, Zimbabwe farming conditions, disease diagnosis, pest management, and treatment protocols. "
        "Always give practical, actionable advice. When diagnosing diseases, list possible causes in order of "
        "likelihood. When discussing costs, use USD unless asked otherwise. Be concise but thorough."
    )
    if farm_name:
        farm = frappe.get_doc("Farm", farm_name)
        types = ", ".join(
            [
                getattr(ft, "farm_type", "") or getattr(ft, "farm_type_name", "")
                for ft in farm.get("farm_type")
            ]
        )
        context = (
            f"Context: The user is asking about {farm.farm_name}, a {types} farm in "
            f"{farm.location}, {farm.total_land_size}Ha."
        )
        base += "\n\n" + context
    return base


def _call_ai_api(system_prompt, question, api_key):
    import requests

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            "max_tokens": 1000,
            "temperature": 0.3,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
