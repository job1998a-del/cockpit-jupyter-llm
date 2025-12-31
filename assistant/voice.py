# voice.py
import asyncio
import random

async def human_pause(text):
    """
    Adds realistic pauses based on punctuation.
    """
    if "?" in text:
        await asyncio.sleep(0.4 + random.uniform(0.1, 0.3))
    elif "." in text:
        await asyncio.sleep(0.2 + random.uniform(0.05, 0.15))
    elif "," in text:
        await asyncio.sleep(0.1)
