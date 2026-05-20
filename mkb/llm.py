import json
import logging
from typing import Optional

import aiohttp

from .config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_API_BASE

logger = logging.getLogger(__name__)


async def evaluate_listing(
    ad_title: str,
    ad_price: str,
    ad_description: str,
    ad_location: str,
    user_prompt: str,
) -> Optional[str]:
    if not LLM_API_KEY and LLM_PROVIDER != "ollama":
        return None
    if not user_prompt.strip():
        return None

    system_prompt = (
        "You evaluate classified ads. "
        "Be concise: 1-2 sentences in the same language as the ad. "
        "Assess whether the listing is a good deal given the user's criteria. "
        'Rate it as "great deal", "fair", or "overpriced". '
        "Respond ONLY with the evaluation, no extra text."
    )

    user_message = (
        f"User criteria: {user_prompt}\n\n"
        f"Listing:\n"
        f"  Title: {ad_title}\n"
        f"  Price: {ad_price}\n"
        f"  Location: {ad_location}\n"
        f"  Description: {ad_description or 'none'}"
    )

    if LLM_PROVIDER == "ollama":
        return await _eval_ollama(system_prompt, user_message)
    elif LLM_PROVIDER == "anthropic":
        return await _eval_anthropic(system_prompt, user_message)
    else:
        return await _eval_openai(system_prompt, user_message)


async def _eval_openai(system: str, user: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            }
            base = LLM_API_BASE or "https://api.openai.com/v1"
            payload = {
                "model": LLM_MODEL or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 200,
                "temperature": 0.3,
            }
            async with session.post(
                f"{base}/chat/completions", headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning("OpenAI error %d: %s", resp.status, text[:200])
                    return None
                data = await resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error("OpenAI eval error: %s", e)
        return None


async def _eval_anthropic(system: str, user: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": LLM_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            payload = {
                "model": LLM_MODEL or "claude-3-haiku-20240307",
                "system": system,
                "messages": [{"role": "user", "content": user}],
                "max_tokens": 200,
                "temperature": 0.3,
            }
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning("Anthropic error %d: %s", resp.status, text[:200])
                    return None
                data = await resp.json()
                return data["content"][0]["text"].strip()
    except Exception as e:
        logger.error("Anthropic eval error: %s", e)
        return None


async def _eval_ollama(system: str, user: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            base = LLM_API_BASE or "http://localhost:11434"
            payload = {
                "model": LLM_MODEL or "llama3.2",
                "system": system,
                "prompt": user,
                "stream": False,
            }
            async with session.post(
                f"{base}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning("Ollama error %d: %s", resp.status, text[:200])
                    return None
                data = await resp.json()
                return data.get("response", "").strip()
    except Exception as e:
        logger.error("Ollama eval error: %s", e)
        return None
