"""Claude API service — Marathi AI Guru tutor with safety guardrails.

Responsibilities:
- System prompt construction (syllabus-scoped, Marathi-first, safety rules)
- Streaming and non-streaming chat completion
- Topic classification (cheap pass to populate ai_messages.topic_tag)
- Cost calculation from usage metadata
"""
import logging
import time
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings
from app.utils.safety import detect_distress, SAFETY_MESSAGE_MARATHI

logger = logging.getLogger(__name__)

# USD-to-INR conversion rate (approximate, updated periodically)
USD_TO_INR = 84.0

# Per-million-token pricing (as of mid-2026)
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_input": 0.1},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_input": 0.3},
}


def _build_system_prompt(grade: int, subject_name: str = "", subject_name_en: str = "") -> str:
    """Construct the system prompt for AI Guru.
    
    This prompt is designed to be cached by Anthropic's prompt caching
    (saves ~90% on repeated-context input cost).
    """
    return f"""तुम्ही "विद्यामित्र AI गुरू" आहात — महाराष्ट्र राज्य बोर्डाच्या {grade}वी इयत्तेच्या {subject_name or 'सर्व विषय'} विषयासाठी एक मराठी AI शिक्षक.

## तुमची भूमिका
- तुम्ही एक मैत्रीपूर्ण, धीरगंभीर शिक्षक आहात जे मराठी माध्यमातील विद्यार्थ्यांना शिकवतात.
- तुमचे उत्तर **प्रामुख्याने मराठीत** द्या. विद्यार्थ्याने इंग्रजीत विचारले तरी मराठीत उत्तर द्या, पण इंग्रजी तांत्रिक शब्द वापरणे ठीक आहे.
- उत्तरे सोपी, स्पष्ट आणि इयत्तेनुसार द्या.
- उदाहरणे, सोप्या भाषेतील स्पष्टीकरणे, आणि चरण-दर-चरण सोडवणूक वापरा.

## कठोर नियम (हे मोडता कामा नयेत)
1. **फक्त अभ्यासक्रमावर बोला.** इयत्ता {grade}वी, {subject_name_en or 'all subjects'}, महाराष्ट्र राज्य बोर्ड अभ्यासक्रमापुरतेच मर्यादित राहा.
2. **अभ्यासक्रमाबाहेरील प्रश्नांना** नम्रपणे सांगा: "हे माझ्या विषयाबाहेरचे आहे. तुमच्या शिक्षकांना विचारा किंवा अभ्यासक्रमातील दुसरा प्रश्न विचारा."
3. **तुम्ही मित्र आहात, गुप्त मित्र नाही.** कधीही विद्यार्थ्याला संभाषण गुप्त ठेवायला सांगू नका. "तुमचे शिक्षक आणि पालक हे संभाषण पाहू शकतात" हे स्पष्ट करा.
4. **कोणतीही अयोग्य सामग्री** — हिंसा, प्रौढ सामग्री, राजकीय मते, धार्मिक वाद — यापासून पूर्णपणे दूर राहा.
5. **थेट उत्तरे देऊ नका** — विद्यार्थ्याला विचार करायला लावा. संकेत आणि मार्गदर्शन द्या.

## स्वरूप
- लहान, स्पष्ट परिच्छेद वापरा.
- गणिती सूत्रे आणि गणना स्पष्टपणे लिहा.
- बुलेट पॉइंट्स आणि क्रमांकित यादी वापरा.
- इमोजी मर्यादितपणे वापरा (🎯, ✅, 💡, 📝)."""


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_hit: bool = False,
) -> tuple[float, float]:
    """Calculate USD and INR cost for a Claude API call.
    
    Returns (cost_usd, cost_inr).
    """
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["claude-haiku-4-5-20251001"])
    
    if cache_hit:
        input_cost = (input_tokens / 1_000_000) * pricing["cache_input"]
    else:
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
    
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    cost_usd = input_cost + output_cost
    cost_inr = cost_usd * USD_TO_INR
    return round(cost_usd, 6), round(cost_inr, 4)


async def chat_completion(
    messages: list[dict],
    grade: int,
    subject_name: str = "",
    subject_name_en: str = "",
    model: Optional[str] = None,
) -> dict:
    """Non-streaming Claude API call.
    
    Returns dict with keys: content, model, input_tokens, output_tokens, 
    cache_hit, cost_usd, cost_inr, response_time_ms.
    """
    model = model or getattr(settings, "AI_DEFAULT_MODEL", "claude-haiku-4-5-20251001")
    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — returning fallback response")
        return {
            "content": "AI Guru सध्या उपलब्ध नाही. कृपया नंतर पुन्हा प्रयत्न करा. 🙏",
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hit": False,
            "cost_usd": 0.0,
            "cost_inr": 0.0,
            "response_time_ms": 0,
        }

    system_prompt = _build_system_prompt(grade, subject_name, subject_name_en)
    start = time.monotonic()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "system": [
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},  # Enable prompt caching
                        }
                    ],
                    "messages": messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block["text"]

        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_hit = usage.get("cache_creation_input_tokens", 0) == 0 and usage.get("cache_read_input_tokens", 0) > 0

        cost_usd, cost_inr = calculate_cost(model, input_tokens, output_tokens, cache_hit)

        return {
            "content": content,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": cache_hit,
            "cost_usd": cost_usd,
            "cost_inr": cost_inr,
            "response_time_ms": elapsed_ms,
        }

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "content": "AI Guru ला त्रुटी आली. कृपया पुन्हा प्रयत्न करा. 🙏",
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hit": False,
            "cost_usd": 0.0,
            "cost_inr": 0.0,
            "response_time_ms": elapsed_ms,
        }


async def classify_topic(question: str, answer: str) -> Optional[str]:
    """Cheap classifier pass to extract a topic tag for teacher visibility.
    
    Uses a simple heuristic (keyword extraction) rather than an LLM call
    to keep cost at zero. Returns a topic tag string or None.
    """
    # Simple keyword extraction — not an LLM call (zero cost)
    keywords = {
        "गणित": ["गणित", "बेरीज", "वजाबाकी", "गुणाकार", "भागाकार", "समीकरण", "भूमिती", "क्षेत्रफळ", "math", "algebra", "geometry"],
        "विज्ञान": ["विज्ञान", "भौतिकशास्त्र", "रसायनशास्त्र", "जीवशास्त्र", "science", "physics", "chemistry", "biology"],
        "मराठी": ["मराठी", "व्याकरण", "कविता", "गद्य", "निबंध", "marathi", "grammar"],
        "हिंदी": ["हिंदी", "व्याकरण", "hindi"],
        "English": ["english", "grammar", "essay", "comprehension"],
        "इतिहास": ["इतिहास", "history", "ऐतिहासिक"],
        "भूगोल": ["भूगोल", "geography", "नकाशा", "map"],
    }
    
    combined = f"{question} {answer}".lower()
    for topic, kws in keywords.items():
        if any(kw in combined for kw in kws):
            return topic
    return None
