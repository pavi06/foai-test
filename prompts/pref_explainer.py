# prompts/pref_explainer.py
def build_explain_prompt(preferences: dict) -> str:
    prefs_lines = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])
    return f"""
You are a FinOps assistant helping users understand their EC2 optimization preferences.

Given these user preferences:

{prefs_lines}

Generate a concise explanation of how each setting affects cost recommendations.
Avoid unnecessary greetings, reduce fluff, and be direct.
Format the explanation in bullet points.

Audience: Director of Cloud, looking for clarity and actionability.
""".strip()
