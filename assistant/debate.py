# debate.py
import logging

logger = logging.getLogger(__name__)

async def internal_debate(query, query_fn):
    """
    Simulates internal debate between two perspectives for better reasoning.
    """
    logger.info("Initiating internal debate...")
    
    # Perspective A: Pro/Confirmation
    pro = await query_fn("phi-2", f"Argue FOR responding positively or taking immediate action on: {query}")
    
    # Perspective B: Con/Caution
    con = await query_fn("phi-2", f"Argue AGAINST or provide a cautionary perspective on: {query}")

    # Synthesis: The final balanced decision
    synthesis_prompt = f"""
    The agent is considering how to respond to: "{query}"

    Internal Debate:
    PRO: {pro}
    CON: {con}

    Combine these into a single, balanced, human-like response:
    """
    
    final_response = await query_fn("tinyllama", synthesis_prompt)
    return final_response.strip()
