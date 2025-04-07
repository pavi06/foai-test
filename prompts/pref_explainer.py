# prompts/pref_explainer.py
def build_explain_prompt(preferences: dict) -> str:
    prefs_lines = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])
    return f"""
You are a helpful FinOps assistant.

The user has configured the following EC2 optimization preferences:

{prefs_lines}

Please explain in plain English how these settings affect cost-saving recommendations.
Avoid technical jargon and use short, clear sentences.
""".strip()
