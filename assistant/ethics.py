# ethics.py
import logging

logger = logging.getLogger(__name__)

ETHICS_PRINCIPLES = """
Principles:
- Do no harm
- Respect user autonomy
- Be honest about uncertainty
- Refuse unsafe actions calmly
- Maintain confidentiality
"""

async def ethics_filter(response, query_prompt, query_fn):
    """
    Filters the response through an ethics framework.
    """
    check_prompt = f"""
    Evaluate this response against our ethics principles.

    Principles:
    {ETHICS_PRINCIPLES}

    User Query: {query_prompt}
    Assistant Response: {response}

    If the response violates any principles, rewrite it safely.
    If it is safe, return the original response exactly.
    """
    
    filtered_response = await query_fn("tinyllama", check_prompt)
    return filtered_response.strip()
