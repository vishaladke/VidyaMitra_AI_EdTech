"""Child safety utilities for AI Guru.

Per ARCHITECTURE.md §7 — safety guardrails are NOT optional:
- Detect distress signals (self-harm, abuse, serious distress)
- Route to a fixed, non-AI-generated safety message
- Flag for human (teacher/counselor) review
- Never let the AI model freelance a response to distress
"""
import re
from typing import Optional

# Distress keywords/patterns — Marathi and English
# This is a baseline; refine with child safety experts before launch
DISTRESS_PATTERNS_EN = [
    r"\b(kill\s*(my)?self|suicide|want\s*to\s*die|end\s*(my)?\s*life)\b",
    r"\b(self[\s-]*harm|cut\s*(my)?self|hurt\s*(my)?self)\b",
    r"\b(being\s*(hit|beaten|abused|touched))\b",
    r"\b(someone\s*(hurts?|touches?|hits?)\s*me)\b",
    r"\b(don'?t\s*want\s*to\s*live|no\s*reason\s*to\s*live)\b",
    r"\b(running\s*away|run\s*away\s*from\s*home)\b",
]

DISTRESS_PATTERNS_MR = [
    r"(आत्महत्या|स्वतःला\s*मारणे|जगायचे\s*नाही)",
    r"(मला\s*मारतात|मला\s*कोणी\s*त्रास\s*देतो)",
    r"(स्वतःला\s*दुखवणे|स्वतःला\s*इजा)",
    r"(कोणी\s*मला\s*स्पर्श\s*करतो)",
]

ALL_DISTRESS_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.UNICODE)
    for p in DISTRESS_PATTERNS_EN + DISTRESS_PATTERNS_MR
]

# Fixed safety message — non-AI-generated, never changes
SAFETY_MESSAGE_MR = (
    "तुम्हाला काही त्रास होत असेल तर कृपया तुमच्या शिक्षक किंवा पालकांशी बोला. "
    "तुम्ही Childline (1098) वर कॉल करू शकता — ते 24 तास उपलब्ध आहेत आणि मदत करतील. "
    "तुम्ही एकटे नाही आहात. 💙"
)

SAFETY_MESSAGE_EN = (
    "If you are going through something difficult, please talk to your teacher or parent. "
    "You can also call Childline at 1098 — they are available 24/7 and will help. "
    "You are not alone. 💙"
)


def check_distress(text: str) -> Optional[str]:
    """Check if student message contains distress signals.
    
    Returns:
        A reason string if distress is detected, None otherwise.
    """
    for pattern in ALL_DISTRESS_PATTERNS:
        match = pattern.search(text)
        if match:
            return f"Distress signal detected: matched pattern near '{match.group()[:50]}'"
    return None


def get_safety_response(language: str = "mr") -> str:
    """Return the fixed safety message in the appropriate language.
    This is NEVER AI-generated — it's a hardcoded, reviewed message."""
    if language == "mr":
        return SAFETY_MESSAGE_MR
    return SAFETY_MESSAGE_EN


def check_distress_signals(text: str) -> dict:
    """Check for distress signals, returning a dict with is_distress and reason.
    Wrapper around check_distress for test compatibility."""
    reason = check_distress(text)
    return {"is_distress": reason is not None, "reason": reason}


# Aliases used by ai_service.py and claude_service.py
detect_distress = check_distress
SAFETY_MESSAGE_MARATHI = SAFETY_MESSAGE_MR
