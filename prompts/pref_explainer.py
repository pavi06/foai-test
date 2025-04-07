# prompts/pref_explainer.py

from langchain_core.prompts import PromptTemplate

# Define persona guidance dictionary
persona_instructions = {
    "engineer": "Use technical but concise language focused on thresholds and optimization triggers.",
    "product_owner": "Explain tradeoffs and how preferences influence cost vs performance.",
    "finance": "Highlight the budget impact and savings logic behind each setting.",
    "executive": "Summarize strategic intent behind these settings in business terms."
}

# LangChain-style prompt template
explain_template = PromptTemplate.from_template("""
You are a FinOps assistant. The user has configured the following EC2 optimization preferences:

{prefs_block}

Audience: {persona_title}
Guidance: {persona_instructions}

Explain in bullet points how these settings influence cost-saving recommendations.
Keep it clear, concise, and role-appropriate.
""".strip())

def build_explain_prompt(preferences: dict, persona: str = "engineer") -> str:
    prefs_block = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])
    persona_key = persona.lower()
    instructions = persona_instructions.get(persona_key, persona_instructions["engineer"])
    return explain_template.format(
        prefs_block=prefs_block,
        persona_title=persona.title(),
        persona_instructions=instructions
    )
