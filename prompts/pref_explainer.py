# prompts/pref_explainer.py

from langchain_core.prompts import PromptTemplate

# Define persona guidance dictionary
persona_instructions = {
    "engineer": "Use concise technical language. Focus on thresholds, metrics, and optimization logic.",
    "product_owner": "Highlight tradeoffs and how user preferences affect performance vs. cost.",
    "finance": "Emphasize budget impact, cost drivers, and potential savings for each setting.",
    "executive": "Summarize high-level strategic benefits and business outcomes of the optimizations."
}



# LangChain-style prompt template
explain_template = PromptTemplate.from_template("""
You are a FinOps assistant.

The user has configured the following **EC2 Optimization Preferences**:
{prefs_block}

**Audience:** {persona_title}  
**Guidance:** {persona_instructions}

Instructions:
- Present insights in clear, **bullet points**.
- Tailor the tone and detail to the **audience**.
- **Explain how each setting contributes to cost savings.**
- Include **specific examples or use cases** where applicable.
- Mention relevant **instance details** (e.g., instance type, usage pattern).
- Avoid generalizations. Be **precise and actionable**.

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
