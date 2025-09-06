from typing import List, Dict, Any
from groq import Groq
from ..core.settings import GROQ_API_KEY, GROQ_MODEL
from ..core.logging import logger


def groq_chat(messages: List[Dict[str, str]], temperature: float = 0.4) -> str:
    """Call Groq using the official groq Python client (non-stream)."""

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=GROQ_API_KEY)

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        reasoning_effort="low",
        top_p=1,
        stream=False,
        stop=None,
    )

    try:
        logger.info(f"Groq response: {completion}")
        return (completion.choices[0].message.content or "").strip()
    except Exception:
        try:
            return str(completion["choices"][0]["message"]["content"]).strip()
        except Exception:
            return ""

