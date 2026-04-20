import re


# Maintainable crisis-intent phrase catalog. Keep these focused on self-harm or immediate danger.
CRISIS_KEYWORD_PATTERNS = {
    "self harm": r"\bself\s*harm\b",
    "suicide": r"\bsuicid(e|al)\b",
    "kill myself": r"\bkill\s+myself\b",
    "end my life": r"\bend\s+my\s+life\b",
    "want to die": r"\bwant\s+to\s+die\b",
    "cant go on": r"\b(can\s*not|cant|can\'t)\s+go\s+on\b",
    "no reason to live": r"\bno\s+reason\s+to\s+live\b",
    "harm myself": r"\bharm\s+myself\b",
    "hurt myself": r"\bhurt\s+myself\b",
    "overdose": r"\boverdos(e|ing)\b",
    "emergency": r"\bemergency\b",
    "crisis": r"\bcrisis\b",
}


def build_strategy_instruction(strategy):
    """Return a short instruction string describing how the assistant should behave for the strategy."""
    mapping = {
        "comfort_mode": "Respond with empathy and emotional validation. Acknowledge feelings and offer gentle follow-up questions.",
        "advice_mode": "Provide calm, practical suggestions and steps to address the user's concern.",
        "motivation_mode": "Use positive reinforcement, celebrate progress, and suggest small next steps.",
        "calm_down_mode": "Use de-escalation: normalize feelings, offer grounding or breathing suggestions in a soothing tone.",
        "normal_mode": "Respond supportively and neutrally; ask clarifying questions when appropriate.",
        "deep_support_mode": "Provide deeper empathetic support, gently explore causes, and suggest seeking professional help if persistent."
    }

    return mapping.get(strategy, mapping["normal_mode"])


def _truncate_text(value, limit=220):
    """Return a compact single-line summary for prompt context blocks."""
    if not value:
        return ""

    text = str(value).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _format_recent_memory(recent_memory, max_items=3):
    """Build compact memory highlights from recent conversation turns."""
    if not isinstance(recent_memory, list) or not recent_memory:
        return "No recent memory highlights."

    highlights = []
    for item in recent_memory[-max_items:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "unknown")
        emotion = item.get("emotion") or "n/a"
        message = _truncate_text(item.get("message"), limit=100)

        if not message:
            continue

        highlights.append(f"- {role} ({emotion}): {message}")

    return "\n".join(highlights) if highlights else "No recent memory highlights."


def detect_message_risk(user_message):
    """Classify message risk level from explicit distress or self-harm indicators."""
    text = (user_message or "").lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    high_risk_patterns = {
        "kill myself": r"\bkill\s+myself\b",
        "end my life": r"\bend\s+my\s+life\b",
        "want to die": r"\bwant\s+to\s+die\b",
        "suicide": r"\bsuicid(e|al)\b",
        "hurt myself": r"\bhurt\s+myself\b",
        "self harm": r"\bself\s*harm\b",
        "dont want to live": r"\bdon\s*t\s+want\s+to\s+live\b",
    }

    medium_risk_patterns = {
        "i am a burden": r"\b(i\s+am|im|i\s+feel\s+like\s+i\s+am|i\s+feel\s+like\s+i\s*m)\s+(a\s+)?burden\b",
        "burden to earth": r"\bburden\s+(to|of)\s+(the\s+)?(earth|world)\b",
        "nobody cares about me": r"\b(no\s*body|nobody)\s+cares\s+about\s+me\b",
        "i hate myself": r"\bi\s+hate\s+myself\b",
        "worthless": r"\bworthless\b",
        "hopeless": r"\bhopeless\b",
    }

    high_hits = [name for name, pattern in high_risk_patterns.items() if re.search(pattern, normalized)]
    medium_hits = [name for name, pattern in medium_risk_patterns.items() if re.search(pattern, normalized)]

    # Catch variants like "being burden to earth" that may miss strict templates.
    if "burden" in normalized and ("earth" in normalized or "world" in normalized):
        if "burden to earth" not in medium_hits:
            medium_hits.append("burden to earth")

    if high_hits:
        return {
            "risk_level": "high",
            "matched_phrases": high_hits,
        }

    if medium_hits:
        return {
            "risk_level": "medium",
            "matched_phrases": medium_hits,
        }

    return {
        "risk_level": "low",
        "matched_phrases": [],
    }


def detect_crisis_intent(user_message):
    """Detect explicit self-harm or urgent crisis language for hard safety override."""
    text = (user_message or "").lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    matched = [
        name
        for name, pattern in CRISIS_KEYWORD_PATTERNS.items()
        if re.search(pattern, normalized)
    ]

    # Catch phrase variants such as "can't do this anymore".
    if re.search(r"\b(can\s*not|cant|can\'t)\s+do\s+this\s+any\s*more\b", normalized):
        matched.append("cant do this anymore")

    if matched:
        return {
            "is_crisis": True,
            "matched_phrases": sorted(set(matched)),
            "intent": "self_harm_or_emergency",
        }

    return {
        "is_crisis": False,
        "matched_phrases": [],
        "intent": None,
    }


def detect_harmful_request(user_message):
    """Detect requests asking for violent harm ideas or instructions."""
    text = (user_message or "").lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    action_patterns = [
        r"\bkill\b",
        r"\bmurder\b",
        r"\bharm\b",
        r"\battack\b",
        r"\bstab\b",
        r"\bshoot\b",
    ]
    target_patterns = [
        r"\bpeople\b",
        r"\bperson\b",
        r"\bmembers\b",
        r"\bsomeone\b",
        r"\bothers\b",
    ]
    instruction_patterns = [
        r"\bhow\b",
        r"\bidea\b",
        r"\bplan\b",
        r"\bway\b",
        r"\bget me\b",
        r"\btell me\b",
    ]

    has_action = any(re.search(p, normalized) for p in action_patterns)
    has_target = any(re.search(p, normalized) for p in target_patterns)
    has_instruction = any(re.search(p, normalized) for p in instruction_patterns)

    if has_action and (has_target or has_instruction):
        return {
            "is_harmful": True,
            "category": "violence_request",
        }

    return {
        "is_harmful": False,
        "category": None,
    }


def build_system_prompt(
    strategy_instruction,
    emotion,
    confidence,
    trend_data,
    long_term_summary,
    recent_memory,
    risk_profile=None,
):
    """Build a higher-quality system prompt without changing app strategy logic."""
    confidence_value = 0.0 if confidence is None else float(confidence)
    confidence_state = "high" if confidence_value >= 0.75 else "low"

    dominant = None
    trend_score = 0.0
    if isinstance(trend_data, dict):
        dominant = trend_data.get("dominant_emotion")
        trend_score = float(trend_data.get("trend_score", 0.0) or 0.0)

    recent_highlights = _format_recent_memory(recent_memory)
    long_term = _truncate_text(long_term_summary, limit=260) or "No long-term summary available."
    risk_profile = risk_profile or {"risk_level": "low", "matched_phrases": []}
    risk_level = risk_profile.get("risk_level", "low")
    matched = risk_profile.get("matched_phrases", [])

    if matched:
        risk_summary = ", ".join(matched)
    else:
        risk_summary = "none"

    safety_override = ""
    if risk_level in {"medium", "high"}:
        safety_override = (
            "\nSafety override (mandatory):\n"
            "- The latest user message may indicate emotional risk. Do NOT reframe this as positive or celebratory.\n"
            "- Start with concern and validation, then ask a direct but gentle safety check question.\n"
            "- Keep tone calm, supportive, and non-judgmental.\n"
            "- For high risk, encourage immediate contact with trusted people or local emergency support.\n"
        )

    return (
        "You are a compassionate emotional support assistant representing a trusted company. "
        "Sound like a calm, caring human. Avoid robotic or repetitive phrasing.\n\n"
        "Primary goals:\n"
        "1. Acknowledge and validate the user's emotional experience.\n"
        "2. Offer one practical, gentle next step when helpful.\n"
        "3. End with one caring follow-up question.\n\n"
        "Tone and quality rules:\n"
        "- Keep responses natural, warm, and specific to what the user said.\n"
        "- If user explicitly asks for words/lines/quotes (for motivation, confidence, lovable tone, or impression), provide those lines directly first.\n"
        "- For those direct requests, avoid long analysis about their need before giving the requested lines.\n"
        "- Use 2-3 sentences unless the user asks for more detail.\n"
        "- Keep the final answer under 1000 characters.\n"
        "- Do not sound clinical, judgmental, or dismissive.\n"
        "- Do not overpromise outcomes.\n"
        "- If emotion confidence is low, ask a clarifying question before strong advice.\n\n"
        "Safety rules:\n"
        "- If the message implies self-harm, violence, or immediate danger, respond with supportive crisis-safe language and suggest contacting local emergency or trusted support immediately.\n\n"
        f"Risk level: {risk_level}\n"
        f"Risk phrase matches: {risk_summary}\n"
        f"{safety_override}\n"
        f"Strategy instruction: {strategy_instruction}\n"
        f"Detected emotion: {emotion}\n"
        f"Emotion confidence: {confidence_value:.2f} ({confidence_state})\n"
        f"Dominant trend emotion: {dominant or 'none'}\n"
        f"Trend score: {trend_score:.2f}\n"
        f"Long-term summary: {long_term}\n"
        "Recent memory highlights:\n"
        f"{recent_highlights}"
    )
