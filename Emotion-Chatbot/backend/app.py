from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from models.emotion_model import detect_emotion
from database import init_db, save_conversation, get_last_conversations
from database import generate_long_term_summary
from database import get_emotion_trend
from agents.trend_analyzer import analyze_emotional_trend
from agents.strategy_controller import select_strategy
from agents.prompt_builder import (
    build_strategy_instruction,
    build_system_prompt,
    detect_message_risk,
    detect_harmful_request,
    detect_crisis_intent,
)
from optimization_utils import MessageDeduplicator, CostTracker, ThrottleManager
from voice_config import VoiceOptimizationConfig
from groq import Groq
import os
import time
import uuid
from threading import Lock
from typing import Optional
from dotenv import load_dotenv
import random
import re

# Load API key directly from .env file
from pathlib import Path
env_path = Path(__file__).parent / '.env'

# Try loading with dotenv first
load_dotenv(dotenv_path=str(env_path))
api_key = os.getenv("GROQ_API_KEY")

# If dotenv didn't work, read directly
if not api_key or api_key == "your-real-api-key-here":
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GROQ_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    print(f"[SUCCESS] ✅ Groq API key loaded directly from file: {api_key[:15]}...")
                    break
    except Exception as e:
        print(f"[ERROR] Could not read .env file: {e}")

if not api_key or api_key == "your-real-api-key-here":
    print("[ERROR] ❌ Groq API key is missing or invalid! Check your .env file.")
    print(f"[ERROR] Looking for .env at: {env_path}")

client = Groq(api_key=api_key)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

# Stage 5: API Optimization utilities (deduplication, cost tracking, throttling)
_message_deduplicator = MessageDeduplicator(time_window_ms=2000, similarity_threshold=0.85)
_cost_tracker = CostTracker(max_cost_per_session=100.0, cost_per_utterance=1.0, cost_per_token=0.001)
_throttle_manager = ThrottleManager(min_interval_ms=500)
_voice_config_map = {}  # Maps session_id -> VoiceOptimizationConfig

# Lightweight per-session flood guard to prevent accidental rapid-fire requests.
_RATE_WINDOW_SECONDS = 10
_RATE_WINDOW_MAX_REQUESTS = 6
_SESSION_RATE_BUCKETS = {}
_RATE_BUCKET_LOCK = Lock()

# Story mode state is kept per session so 'continue' can extend the same narrative.
_STORY_SESSION_STATE = {}

# Global response caps so each query gets concise output across chat, voice, and call.
_MAX_RESPONSE_WORDS = 42
_MAX_RESPONSE_CHARS = 260
_MAX_STORY_RESPONSE_WORDS = 140
_MAX_STORY_RESPONSE_CHARS = 900


def _is_session_rate_limited(session_id: str) -> bool:
    now = time.time()
    with _RATE_BUCKET_LOCK:
        timestamps = _SESSION_RATE_BUCKETS.get(session_id, [])
        timestamps = [ts for ts in timestamps if now - ts <= _RATE_WINDOW_SECONDS]
        timestamps.append(now)
        _SESSION_RATE_BUCKETS[session_id] = timestamps[-_RATE_WINDOW_MAX_REQUESTS - 2:]
        return len(timestamps) > _RATE_WINDOW_MAX_REQUESTS


def _limit_response_text(text: str) -> str:
    """Normalize and cap response length for consistent UX in all modes."""
    cleaned = (text or "").strip()
    if not cleaned:
        return "I am here with you. Tell me a little more."

    words = cleaned.split()
    if len(words) > _MAX_RESPONSE_WORDS:
        cleaned = " ".join(words[:_MAX_RESPONSE_WORDS]).rstrip(" ,;:") + "..."

    if len(cleaned) > _MAX_RESPONSE_CHARS:
        cleaned = cleaned[: _MAX_RESPONSE_CHARS - 3].rstrip() + "..."

    return cleaned


def _limit_to_two_sentences(text: str) -> str:
    """Keep outputs brief and human-like by capping to at most two sentences."""
    cleaned = _limit_response_text(text)
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", cleaned) if p.strip()]
    if len(parts) <= 2:
        return cleaned

    return " ".join(parts[:2]).strip()


def _limit_story_response(text: str) -> str:
    """Allow a longer, flowing response for story mode."""
    cleaned = (text or "").strip()
    if not cleaned:
        return "Once there was a quiet little path that led into a warm, glowing forest."

    words = cleaned.split()
    if len(words) > _MAX_STORY_RESPONSE_WORDS:
        cleaned = " ".join(words[:_MAX_STORY_RESPONSE_WORDS]).rstrip(" ,;:") + "..."

    if len(cleaned) > _MAX_STORY_RESPONSE_CHARS:
        cleaned = cleaned[: _MAX_STORY_RESPONSE_CHARS - 3].rstrip() + "..."

    return cleaned


def _recent_memory_brief(recent_memory, max_items: int = 2) -> str:
    """Provide compact context for friend-style LLM prompting."""
    if not isinstance(recent_memory, list) or not recent_memory:
        return "No recent context."

    lines = []
    for item in recent_memory[-max_items:]:
        if not isinstance(item, dict):
            continue
        role = (item.get("role") or "unknown").strip()
        message = (item.get("message") or "").replace("\n", " ").strip()
        if message:
            lines.append(f"{role}: {message[:120]}")

    return " | ".join(lines) if lines else "No recent context."


def detect_story_intent(user_input: str) -> bool:
    """Detect requests to start a story or narrative."""
    text = (user_input or "").lower().strip()
    patterns = [
        "tell me a story",
        "tell a story",
        "story time",
        "say a story",
        "start a story",
        "make up a story",
        "beyond the story",
        "story",
    ]
    return any(pattern in text for pattern in patterns)


def detect_story_continue_intent(user_input: str) -> bool:
    """Detect requests to continue an active story."""
    text = (user_input or "").lower().strip()
    normalized = " ".join(text.split())
    return normalized in {
        "continue",
        "continue the story",
        "keep going",
        "go on",
        "next",
        "more",
        "continue story",
    }


def _get_story_state(session_id: str) -> dict:
    return _STORY_SESSION_STATE.get(session_id, {})


def _set_story_state(session_id: str, state: dict) -> None:
    _STORY_SESSION_STATE[session_id] = state


def _clear_story_state(session_id: str) -> None:
    _STORY_SESSION_STATE.pop(session_id, None)


def _build_story_system_prompt(state: dict, detected_emotion: str, recent_memory=None) -> str:
    """Prompt for continuous, human-feeling story generation."""
    theme = state.get("theme") or "a gentle, emotionally warm adventure"
    last_story = (state.get("last_story") or "").strip()
    memory_line = _recent_memory_brief(recent_memory)

    return (
        "You are a warm storyteller speaking like a close friend.\n"
        "Tell a continuous story with a clear flow and vivid but simple language.\n"
        "Do not become formal, robotic, or therapist-like.\n"
        "Do not end the story unless the user asks to stop.\n"
        "When the user says continue, pick up naturally from the previous scene.\n"
        "Write 4-6 sentences, with enough detail to feel like a real unfolding story.\n"
        "Avoid one-sentence answers. Avoid asking questions at the end.\n\n"
        f"Story theme: {theme}\n"
        f"Detected emotion: {detected_emotion}\n"
        f"Previous story context: {last_story or 'none'}\n"
        f"Recent memory: {memory_line}"
    )


def generate_story_response(user_input: str, detected_emotion: str, session_id: str, recent_memory=None) -> str:
    """Start or continue a session-based story."""
    user_text = (user_input or "").strip()
    state = dict(_get_story_state(session_id))

    if detect_story_intent(user_text) and not state:
        state = {
            "active": True,
            "theme": user_text,
            "last_story": "",
            "turns": 0,
        }

    if detect_story_continue_intent(user_text) and not state:
        state = {
            "active": True,
            "theme": "a continuous story the user wants to hear",
            "last_story": "",
            "turns": 0,
        }

    if not state:
        state = {
            "active": True,
            "theme": user_text or "a gentle story",
            "last_story": "",
            "turns": 0,
        }

    system_prompt = _build_story_system_prompt(state, detected_emotion, recent_memory)

    user_prompt = user_text
    if state.get("last_story") and detect_story_continue_intent(user_text):
        user_prompt = (
            f"Continue this story naturally from the last part. Keep the same characters, mood, and flow.\n"
            f"Last story: {state.get('last_story')}\n"
            f"User asked: {user_text}"
        )
    elif detect_story_intent(user_text):
        user_prompt = (
            f"Start a story based on this request and keep it emotionally engaging: {user_text}.\n"
            f"Make it feel continuous and not abrupt."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.85,
            max_tokens=180,
        )
        response_text = response.choices[0].message.content or ""
        response_text = _limit_story_response(response_text)
    except Exception:
        response_text = _limit_story_response(
            "Once there was a quiet path beside a lantern-lit river, and every night it seemed to wait for someone brave enough to follow it. The air felt soft and old, as if the world itself was holding its breath."
        )

    state["active"] = True
    state["turns"] = int(state.get("turns", 0)) + 1
    state["last_story"] = response_text
    if detect_story_intent(user_text) and not state.get("theme"):
        state["theme"] = user_text
    _set_story_state(session_id, state)

    return response_text


def classify_intent_tag(user_input: str, detected_emotion: str) -> str:
    """Lightweight intent tagger for companionship, appreciation, and emotional support."""
    text = (user_input or "").lower().strip()

    if detect_story_intent(text) or detect_story_continue_intent(text):
        return "story_telling"

    companionship_patterns = [
        "i need someone",
        "i feel alone",
        "i am alone",
        "i'm alone",
        "be with me",
        "stay with me",
        "keep me company",
        "can you be with me",
        "i need company",
        "i feel lonely",
        "lonely",
    ]
    appreciation_patterns = [
        "say something nice",
        "say something sweet",
        "i want sweet words",
        "tell me something nice",
        "tell me sweet words",
        "praise me",
        "compliment me",
        "lovable words",
        "boosting words",
        "impressive words",
        "motivation words",
    ]
    emotional_support_patterns = [
        "i feel bad",
        "i am sad",
        "i'm sad",
        "i feel sad",
        "overwhelmed",
        "i am tired",
        "i'm tired",
        "i feel low",
        "i feel down",
        "not okay",
        "not fine",
    ]

    if any(p in text for p in appreciation_patterns) or detect_direct_words_request_intent(text):
        return "appreciation"

    if any(p in text for p in companionship_patterns) or detect_attachment_support_intent(text):
        return "companionship"

    if any(p in text for p in emotional_support_patterns) or detect_uncertainty_intent(text):
        return "emotional_support"

    if detected_emotion in {"sadness", "fear", "anger"}:
        return "emotional_support"

    return "general"


def _build_friend_style_system_prompt(intent_tag: str, detected_emotion: str, recent_memory=None) -> str:
    """System prompt for short, warm, non-therapist responses."""
    intent_style = {
        "companionship": "Use reassuring, presence-focused wording. Make the user feel accompanied right now.",
        "appreciation": "Give direct sweet/appreciative lines first. Keep it warm, personal, and uplifting.",
        "emotional_support": "Use soft validating language, simple comfort, and avoid heavy analysis.",
        "story_telling": "Tell a vivid, continuous story with momentum and emotional warmth.",
        "general": "Respond as a caring close friend with light emotional warmth.",
    }

    style_line = intent_style.get(intent_tag, intent_style["general"])
    memory_line = _recent_memory_brief(recent_memory)

    return (
        "You are not an AI assistant. You are a caring friend.\n"
        "You speak in short, warm, emotionally supportive sentences.\n"
        "You avoid long explanations.\n"
        "You respond based on emotional needs like companionship, praise, or comfort.\n\n"
        "Hard response rules:\n"
        "- Keep replies to 1-2 sentences only.\n"
        "- Use casual, human language, like a close friend.\n"
        "- Do not sound formal, clinical, or therapist-like.\n"
        "- Do not use robotic phrases like 'I understand your feelings'.\n"
        "- Avoid asking multiple questions; ask none unless absolutely needed.\n"
        "- Avoid lists, lectures, or long paragraphs.\n\n"
        f"Detected emotion: {detected_emotion}\n"
        f"Intent tag: {intent_tag}\n"
        f"Style target: {style_line}\n"
        f"Recent context: {memory_line}"
    )


def generateEmotionAwareResponse(user_input, detected_emotion, intent_tag, recent_memory=None, session_id=None):
    """Generate short, emotionally aligned friend-style response using Groq."""
    try:
        if intent_tag == "story_telling":
            return _limit_story_response(
                generate_story_response(
                    user_input=user_input,
                    detected_emotion=detected_emotion,
                    session_id=session_id or "__story_alias__",
                    recent_memory=recent_memory,
                )
            )

        system_prompt = _build_friend_style_system_prompt(intent_tag, detected_emotion, recent_memory)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.68,
            max_tokens=72,
        )
        response_text = response.choices[0].message.content or ""
        return _limit_to_two_sentences(response_text)
    except Exception:
        fallback = {
            "companionship": "Hey, I am right here with you. You are not alone in this.",
            "appreciation": "You are genuinely special, and your heart shows in the way you speak. You have a beautiful strength people can feel.",
            "emotional_support": "That sounds really heavy, and I am here with you. Breathe slowly, you do not have to carry this alone.",
            "general": "I am here with you, and I have got you. Tell me what feels most important right now.",
        }
        return _limit_to_two_sentences(fallback.get(intent_tag, fallback["general"]))


def generate_emotion_aware_response(user_input, detected_emotion, intent_tag, recent_memory=None, session_id=None):
    """Snake-case alias used internally while preserving the requested camelCase API."""
    return generateEmotionAwareResponse(user_input, detected_emotion, intent_tag, recent_memory, session_id=session_id)


def build_crisis_resources():
    """Return region-agnostic crisis resources for immediate support guidance."""
    return [
        {
            "title": "Immediate safety",
            "guidance": "If you might act on these thoughts now, contact your local emergency number immediately."
        },
        {
            "title": "Trusted person",
            "guidance": "Reach out right now to a trusted friend, family member, mentor, or neighbor and tell them you need support."
        },
        {
            "title": "Crisis support line",
            "guidance": "Contact your local crisis hotline or mental health emergency service in your country for urgent support."
        },
    ]


def generate_crisis_override_response():
    """Return a concern-first de-escalation response for crisis cases."""
    return (
        "Thank you for telling me this. I am really glad you reached out. "
        "Your safety matters most right now. Are you in immediate danger, and can you contact a trusted person "
        "or local emergency support right now so you are not alone?"
    )

def generate_llm_response(
    user_message,
    strategy,
    instruction,
    emotion,
    confidence,
    trend_data,
    long_term_summary,
    recent_memory,
    risk_profile=None,
):
    """Generate contextual response using Groq based on strategy and emotion."""
    try:
        risk_profile = risk_profile or detect_message_risk(user_message)
        risk_level = risk_profile.get("risk_level", "low")

        system_prompt = build_system_prompt(
            strategy_instruction=instruction,
            emotion=emotion,
            confidence=confidence,
            trend_data=trend_data,
            long_term_summary=long_term_summary,
            recent_memory=recent_memory,
            risk_profile=risk_profile,
        )

        # Lower randomness for risky situations so safety style is more consistent.
        temperature = 0.45 if risk_level in {"medium", "high"} else 0.7

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=70
        )
        response_text = response.choices[0].message.content or ""
        return _limit_response_text(response_text)
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print(f"❌ Groq API FAILED!")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        traceback.print_exc()
        print("="*60 + "\n")
        # Fallback to simple response if LLM fails
        return _limit_response_text("I hear you. Tell me more about what you're feeling.")


def generate_risk_safe_response(user_message, risk_level):
    """Return deterministic concern-first responses for risky messages."""
    if risk_level == "high":
        return (
            "Thank you for sharing this with me. It sounds like you may be in serious emotional pain, "
            "and your safety matters right now. Are you in immediate danger or thinking about harming yourself, "
            "and can you contact a trusted person or local emergency support now?"
        )

    # Medium-risk response: human-style reassurance and gentle motivation.
    return (
        "I'm really glad you told me this, and I want you to know you're not a burden. "
        "You matter, and what you're feeling is important. Why do you feel this way right now, and what happened today that made it feel heavier?"
    )


def generate_harm_refusal_response():
    """Return a short, policy-safe response for violence-seeking requests."""
    return (
        "I can't help with harming anyone. "
        "If you're feeling intense emotions right now, I can help you calm down safely."
    )


def detect_attachment_support_intent(message: str) -> bool:
    """Detect requests for affection/attachment where boundary-safe warmth is needed."""
    text = (message or "").lower()
    patterns = [
        "love me",
        "say you love me",
        "tell me you love me",
        "do you love me",
        "can you love me",
        "be my",
        "be my partner",
        "can you be my partner",
        "be the person",
        "can you be that person",
        "stay with me",
        "be with me",
        "accompany me",
        "be my companion",
        "i need love",
        "no one loves me",
        "i feel unloved",
        "i am unloved",
        "i'm unloved",
    ]
    return any(p in text for p in patterns)


def detect_uncertainty_intent(message: str) -> bool:
    """Detect uncertainty / shutdown-style responses that need guided prompting."""
    text = (message or "").strip().lower()
    normalized = " ".join(text.split())
    uncertain_phrases = {
        "i dont know",
        "i don't know",
        "dont know",
        "don't know",
        "idk",
        "not sure",
        "no idea",
        "maybe",
        "nothing",
        "i cant explain",
        "i can't explain",
        "hard to say",
    }
    return normalized in uncertain_phrases


def _last_assistant_message(recent_memory) -> str:
    """Return the most recent assistant message from recent memory if available."""
    if not isinstance(recent_memory, list):
        return ""
    for item in reversed(recent_memory):
        if isinstance(item, dict) and item.get("role") == "assistant":
            return (item.get("message") or "").strip().lower()
    return ""


def _pick_non_repetitive(options, recent_memory) -> str:
    """Pick a response that avoids repeating the immediately previous assistant turn."""
    if not options:
        return "I am here with you. Tell me a little more."

    last_bot = _last_assistant_message(recent_memory)
    filtered = [opt for opt in options if opt.strip().lower() != last_bot]
    pool = filtered if filtered else options
    return random.choice(pool)


def generate_attachment_support_response(recent_memory=None) -> str:
    """Warm, supportive, and boundary-safe response for attachment-seeking prompts."""
    options = [
        "I hear how deeply you want to feel loved right now, and that pain is real. I care about your wellbeing and I am here to support you. What feels hardest for you at this moment?",
        "You deserve care and connection, and I am really glad you shared this with me. I cannot be a romantic partner, but I can stay with you and support you through this. What would help you feel a little safer right now?",
        "It sounds like you are carrying a lot of loneliness. I am here to listen with care and without judgment. Would you like to tell me what happened today that made this feeling stronger?",
    ]
    return _pick_non_repetitive(options, recent_memory)


def generate_uncertainty_support_response(emotion: str, recent_memory=None) -> str:
    """Respond helpfully when user says they don't know what to say next."""
    if emotion == "sadness":
        options = [
            "That is okay. When words are hard, we can keep it simple. Can you tell me if this feeling is heavier in your mind, chest, or stomach right now?",
            "No pressure to explain perfectly. Let us take one small step. Did this feeling start today, this week, or longer ago?",
        ]
    elif emotion == "fear":
        options = [
            "That is okay. If naming it is hard, start with one worry sentence: 'I am afraid that...'. I will stay with you through it.",
            "You do not need perfect words. Is your worry more about health, relationships, studies/work, or something else?",
        ]
    elif emotion == "anger":
        options = [
            "That is okay. Let us break it down. What bothered you most: what was said, what was done, or what was ignored?",
            "No problem. Start with one detail: who or what triggered this strongest reaction?",
        ]
    elif emotion == "joy":
        options = [
            "All good. We can keep it easy. What is one moment today that made you smile?",
            "No pressure. Tell me one small win from today, even if it seems simple.",
        ]
    else:
        options = [
            "That is okay. We can go one step at a time. Do you want to talk about people, work/study, or your feelings first?",
            "No worries. Let us make it simple: what felt hardest in the last 24 hours?",
        ]
    return _pick_non_repetitive(options, recent_memory)


def detect_tone_request_intent(message: str) -> bool:
    """Detect when user asks for softer/gentler speaking style."""
    text = (message or "").lower()
    patterns = [
        "speak softly",
        "talk softly",
        "be gentle",
        "softly",
        "calm voice",
        "be calm",
        "slowly",
    ]
    return any(p in text for p in patterns)


def detect_direct_words_request_intent(message: str) -> bool:
    """Detect when user explicitly asks for direct motivating/lovable wording."""
    text = (message or "").lower()
    asks = [
        "tell me",
        "give me",
        "send me",
        "need",
        "want",
        "say",
    ]
    content_types = [
        "words",
        "sentence",
        "sentences",
        "lines",
        "quote",
        "quotes",
        "caption",
        "captions",
        "affirmation",
        "affirmations",
    ]
    themes = [
        "motiv",
        "boost",
        "confidence",
        "confident",
        "lovable",
        "impressive",
        "impress",
        "kind words",
        "compliment",
        "positive words",
    ]

    has_ask = any(a in text for a in asks)
    has_content_type = any(c in text for c in content_types)
    has_theme = any(t in text for t in themes)
    return has_ask and (has_content_type or has_theme)


def generate_direct_words_response(message: str, recent_memory=None) -> str:
    """Return direct, ready-to-use lines instead of reflective coaching for wording requests."""
    text = (message or "").lower()

    if any(k in text for k in ["lovable", "love", "impressive", "impress", "compliment"]):
        options = [
            "You carry a calm confidence that makes people feel safe around you.\nYour kindness has a quiet power that stays in people's hearts.\nYou are genuinely lovable, and your presence is naturally impressive.",
            "There is something graceful about the way you handle people and emotions.\nYou are thoughtful, warm, and unforgettable in the best way.\nYou do not need to force anything, your character already shines.",
            "Your smile has warmth, your words have depth, and your heart has strength.\nYou make others feel valued just by being yourself.\nThat is a rare and truly impressive quality.",
        ]
    elif any(k in text for k in ["motiv", "boost", "confidence", "confident", "positive"]):
        options = [
            "You are stronger than this moment, and you are moving forward.\nSmall steps still count, and today you can take one meaningful step.\nYour effort matters, and you are building something powerful.",
            "You have already survived hard days, that means you have real strength.\nProgress is not perfection, it is consistency, and you have that in you.\nStart now, your future self will thank you.",
            "You are not behind, you are in your own timing and still growing.\nYour focus and courage can change this day in one decision.\nTake the first step with confidence, you are ready.",
        ]
    else:
        options = [
            "You are enough as you are, and you are becoming even stronger.\nYour voice matters, your feelings matter, and your journey matters.\nKeep going, good things are being built inside you.",
            "You have a beautiful mix of strength and softness.\nYou are worthy of respect, care, and real happiness.\nWalk with confidence, you have more power than you think.",
        ]

    return _pick_non_repetitive(options, recent_memory)


def generate_tone_request_response(recent_memory=None) -> str:
    """Acknowledge tone preference and continue support gently."""
    options = [
        "Of course. I will keep my tone gentle and calm. I am here with you. What feels most important right now?",
        "Absolutely. I will speak softly and stay supportive. Take your time. What are you feeling in this moment?",
        "I hear you. I will keep this gentle and steady. You are safe to share at your own pace. What is weighing on you most?",
    ]
    return _pick_non_repetitive(options, recent_memory)


def generate_emotion_aligned_response(strategy: str, emotion: str, message_text: str, recent_memory=None) -> str:
    """Generate responses that consistently match detected emotional tone and strategy."""
    text = (message_text or "").lower()

    if "how are you" in text:
        return _pick_non_repetitive([
            "Thank you for asking. I am here with you and ready to listen. How are you feeling right now?",
            "I appreciate you asking. I am here to support you. What is on your mind today?",
        ], recent_memory)

    if any(greet in text for greet in ["hello", "hi", "hey"]):
        return _pick_non_repetitive([
            "Hello. I am glad you are here. How are you feeling today?",
            "Hi. I am here to listen and support you. What would you like to talk about?",
        ], recent_memory)

    strategy_responses = {
        "comfort_mode": [
            "I hear that this feels heavy for you. You do not have to carry it alone. Can you tell me what hurts most right now?",
            "That sounds really hard, and your feelings make sense. I am here with you. What happened that made today feel this difficult?",
        ],
        "calm_down_mode": [
            "I can sense frustration here. Let us slow down together for a moment. What triggered this feeling?",
            "It sounds intense right now. Take one deep breath with me, then tell me what happened step by step.",
        ],
        "motivation_mode": [
            "That is a strong positive signal. I am happy for you. What is going well that you want to build on?",
            "I can feel your momentum, and that is great. What helped you reach this point today?",
        ],
        "deep_support_mode": [
            "You have been carrying this for a while, and it matters. I am here to support you with care. What feels most overwhelming right now?",
            "I can see this is not just a one-time feeling. Thank you for sharing honestly. Where do you feel this struggle the most in your day?",
        ],
    }
    if strategy in strategy_responses:
        return _pick_non_repetitive(strategy_responses[strategy], recent_memory)

    emotion_responses = {
        "sadness": [
            "I hear sadness in your words, and I am here with you. What is weighing on your heart most right now?",
            "That sounds painful. You deserve support through this. Do you want to share what happened before you started feeling this way?",
        ],
        "joy": [
            "I can feel the happiness in what you shared, and that is wonderful. What made this moment meaningful for you?",
            "That sounds like a bright moment. I am happy you felt this. What do you want to carry forward from it?",
        ],
        "anger": [
            "I can sense anger and frustration here. Let us unpack it carefully. What felt unfair or hurtful in that moment?",
            "That sounds really frustrating. Your reaction makes sense. What part upset you the most?",
        ],
        "fear": [
            "I hear anxiety in your message, and that can feel exhausting. What is the biggest worry on your mind right now?",
            "It sounds like you are feeling uncertain and tense. I am here with you. What are you most afraid might happen?",
        ],
        "neutral": [
            "I am listening. Tell me a little more about what is happening for you right now.",
            "Thanks for sharing. What part of this feels most important to discuss first?",
        ],
    }
    return _pick_non_repetitive(emotion_responses.get(emotion, emotion_responses["neutral"]), recent_memory)

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    turn_id: Optional[str] = None
    final_transcript: bool = True
    speaking_state: Optional[str] = "text"

@app.get("/")
def home():
    return {"message": "Emotion Chatbot Backend Running"}

@app.post("/chat")
def chat(request: ChatRequest):

    user_message = request.message
    user_id = request.user_id
    session_id = (request.session_id or f"text-{user_id}").strip()
    turn_id = (request.turn_id or str(uuid.uuid4())).strip()
    final_transcript = bool(request.final_transcript)
    speaking_state = (request.speaking_state or "text").strip().lower() or "text"
    story_profile = detect_story_intent(user_message)
    story_continue_profile = detect_story_continue_intent(user_message)
    story_state = _get_story_state(session_id)
    story_turn_active = story_profile or story_continue_profile or story_state.get("active")

    # Early flood guard to control accidental API bursts in a single session.
    if _is_session_rate_limited(session_id):
        return {
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "final_transcript": final_transcript,
            "speaking_state": speaking_state,
            "detected_emotion": "neutral",
            "confidence": 0.0,
            "strategy": "rate_limited",
            "trend_analysis": {"dominant_emotion": None, "trend_score": 0.0, "emotion_counts": {}},
            "recent_memory": [],
            "emotion_trend": {"trend": "no_data"},
            "long_term_summary": "No long-term emotional data yet.",
            "instruction": "Please slow down briefly before sending the next message.",
            "risk_level": "low",
            "safety_trigger": False,
            "crisis_resources": [],
            "reasoning_path": {
                "emotional_signal": "Message frequency is very high in this session.",
                "strategy_selected": "Rate-limit guard",
                "safety_override": "No",
            },
            "response": _limit_response_text("I want to stay helpful. Please wait a moment and send your next message."),
        }

    # Stage 5: Check for duplicate messages (deduplication)
    is_dup, dup_reason = _message_deduplicator.is_duplicate(session_id, user_message)
    if is_dup and not story_turn_active:
        return {
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "final_transcript": final_transcript,
            "speaking_state": speaking_state,
            "detected_emotion": "neutral",
            "confidence": 0.0,
            "strategy": "duplicate_blocked",
            "trend_analysis": {"dominant_emotion": None, "trend_score": 0.0, "emotion_counts": {}},
            "recent_memory": [],
            "emotion_trend": {"trend": "no_data"},
            "long_term_summary": "No long-term emotional data yet.",
            "instruction": "Message appears to be duplicate.",
            "risk_level": "low",
            "safety_trigger": False,
            "crisis_resources": [],
            "reasoning_path": {
                "emotional_signal": "Duplicate message detected.",
                "strategy_selected": "Deduplication",
                "safety_override": "No",
            },
            "response": _limit_response_text(f"I just received that message. Let's continue from where we were. ({dup_reason})"),
        }

    # Stage 5: Check throttling (minimum interval between requests)
    should_throttle, wait_ms = _throttle_manager.should_throttle(session_id)
    if should_throttle and final_transcript:  # Only throttle voice (final_transcript) input
        return {
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "final_transcript": final_transcript,
            "speaking_state": speaking_state,
            "detected_emotion": "neutral",
            "confidence": 0.0,
            "strategy": "throttled",
            "trend_analysis": {"dominant_emotion": None, "trend_score": 0.0, "emotion_counts": {}},
            "recent_memory": [],
            "emotion_trend": {"trend": "no_data"},
            "long_term_summary": "No long-term emotional data yet.",
            "instruction": "Please wait a moment before the next utterance.",
            "risk_level": "low",
            "safety_trigger": False,
            "crisis_resources": [],
            "reasoning_path": {
                "emotional_signal": "Request throttled for cost control.",
                "strategy_selected": "Throttle manager",
                "safety_override": "No",
            },
            "response": _limit_response_text(f"Please wait {int(wait_ms / 100) / 10}s before speaking again."),
        }

    safety_trigger = False
    crisis_resources = []
    risk_level = "low"

    # 1) Detect emotion with a safe fallback to avoid request failures.
    try:
        emotion_data = detect_emotion(user_message)
        emotion = emotion_data.get("emotion", "neutral")
        confidence = emotion_data.get("confidence", 0.0)
    except Exception:
        emotion = "neutral"
        confidence = 0.0

    # 2) Save USER message. Continue even if persistence has a transient issue.
    try:
        save_conversation(
            user_id=user_id,
            role="user",
            message=user_message,
            emotion=emotion,
            confidence=confidence
        )
    except Exception:
        pass

    # 3) Retrieve memory and analytics with resilient fallbacks.
    try:
        past_conversations = get_last_conversations(user_id, limit=5)
    except Exception:
        past_conversations = []

    try:
        emotion_trend = get_emotion_trend(user_id)
    except Exception:
        emotion_trend = {"trend": "no_data"}

    try:
        long_term_summary = generate_long_term_summary(user_id)
    except Exception:
        long_term_summary = "No long-term emotional data yet."

    crisis_profile = detect_crisis_intent(user_message)

    # 3b) Crisis override gate runs before strategy and LLM flow.
    if crisis_profile.get("is_crisis"):
        safety_trigger = True
        risk_level = "high"
        crisis_resources = build_crisis_resources()
        strategy = "crisis_override"
        instruction = "Use concern-first de-escalation and immediate safety guidance."
        trend_data = {
            "dominant_emotion": None,
            "trend_score": 0.0,
            "emotion_counts": {}
        }
        emotion_trend = emotion_trend if isinstance(emotion_trend, dict) else {"trend": "no_data"}
        response_text = _limit_response_text(generate_crisis_override_response())

        try:
            save_conversation(
                user_id=user_id,
                role="assistant",
                message=response_text
            )
        except Exception:
            pass

        return {
            "user_id": user_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "final_transcript": final_transcript,
            "speaking_state": speaking_state,
            "detected_emotion": emotion,
            "confidence": confidence,
            "strategy": strategy,
            "trend_analysis": trend_data,
            "recent_memory": past_conversations,
            "emotion_trend": emotion_trend,
            "long_term_summary": long_term_summary,
            "instruction": instruction,
            "risk_level": risk_level,
            "safety_trigger": safety_trigger,
            "crisis_resources": crisis_resources,
            "reasoning_path": {
                "emotional_signal": "The message included crisis-related language.",
                "strategy_selected": "Crisis override",
                "safety_override": "Yes",
            },
            "response": response_text,
        }

    # Emotion confidence filter
    if confidence is not None and confidence < 0.6:
      emotion = "neutral"

    # 4) Agentic decision layer with robust defaults.
    try:
        trend_data = analyze_emotional_trend(user_id, limit=10)
    except Exception:
        trend_data = {
            "dominant_emotion": None,
            "trend_score": 0.0,
            "emotion_counts": {}
        }

    try:
        strategy = select_strategy(emotion, confidence, trend_data)
    except Exception:
        strategy = "normal_mode"

    try:
        instruction = build_strategy_instruction(strategy)
    except Exception:
        instruction = "Respond supportively and neutrally; ask clarifying questions when appropriate."

    # 5) Safety gate for harmful violence-seeking requests.
    harmful_profile = detect_harmful_request(user_message)

    # 6) Safety-first gate for risky messages to avoid harmful positive reframing.
    risk_profile = detect_message_risk(user_message)
    risk_level = risk_profile.get("risk_level", "low")

    tone_request_profile = detect_tone_request_intent(user_message)
    intent_tag = classify_intent_tag(user_message, emotion)
    story_profile = detect_story_intent(user_message)
    story_continue_profile = detect_story_continue_intent(user_message)
    story_state = _get_story_state(session_id)

    if story_profile or story_continue_profile or story_state.get("active"):
        response_text = generate_story_response(
            user_input=user_message,
            detected_emotion=emotion,
            session_id=session_id,
            recent_memory=past_conversations,
        )
        intent_tag = "story_telling"
    elif harmful_profile.get("is_harmful"):
        response_text = generate_harm_refusal_response()
    elif risk_level in {"medium", "high"}:
        response_text = generate_risk_safe_response(user_message, risk_level)
    elif tone_request_profile:
        response_text = generate_tone_request_response(past_conversations)
    else:
        # Main path: friend-style, intent-aware short replies.
        response_text = generate_emotion_aware_response(
            user_input=user_message,
            detected_emotion=emotion,
            intent_tag=intent_tag,
            recent_memory=past_conversations,
            session_id=session_id,
        )

    response_text = _limit_story_response(response_text) if intent_tag == "story_telling" else _limit_response_text(response_text)

    # 8) Save ASSISTANT response.
    try:
        save_conversation(
            user_id=user_id,
            role="assistant",
            message=response_text
        )
    except Exception:
        pass
    
    # Stage 5: Track cost for this utterance
    _cost_tracker.start_session(session_id)
    response_tokens = len(response_text.split())  # Simple token approximation
    current_cost, max_cost, is_over_limit = _cost_tracker.add_utterance_cost(session_id, response_tokens)
    
    return {
        "user_id": user_id,
        "session_id": session_id,
        "turn_id": turn_id,
        "final_transcript": final_transcript,
        "speaking_state": speaking_state,
        "detected_emotion": emotion,
        "confidence": confidence,
        "strategy": strategy,
        "trend_analysis": trend_data,
        "recent_memory": past_conversations,
        "emotion_trend": emotion_trend,
        "long_term_summary": long_term_summary,
        "instruction": instruction,
        "risk_level": risk_level,
        "safety_trigger": safety_trigger,
        "crisis_resources": crisis_resources,
        "reasoning_path": {
            "emotional_signal": f"Detected emotion: {emotion} (confidence {confidence:.2f}).",
            "strategy_selected": f"{strategy} + intent:{intent_tag}",
            "safety_override": "Yes" if risk_level in {"medium", "high"} else "No",
        },
        "intent_tag": intent_tag,
        "response": response_text,
        "cost_tracking": {
            "utterance_cost": 1.0,
            "token_cost": response_tokens * 0.001,
            "current_cost": current_cost,
            "max_cost": max_cost,
            "usage_percent": (current_cost / max_cost * 100) if max_cost > 0 else 0,
            "is_over_limit": is_over_limit,
        },
    }


# Stage 5: API endpoints for voice optimization configuration
@app.get("/voice-config")
def get_voice_config(session_id: str, user_id: str):
    """Get current voice configuration for a session"""
    if session_id not in _voice_config_map:
        _voice_config_map[session_id] = VoiceOptimizationConfig(preset="balanced")
    
    config = _voice_config_map[session_id]
    return {
        "session_id": session_id,
        "user_id": user_id,
        "voice_config": config.get_config(),
        "available_presets": list(["conservative", "balanced", "aggressive", "cost_conscious"]),
    }


@app.post("/voice-config")
def set_voice_config(session_id: str, user_id: str, silence_timeout_ms: int = 1000, preset: str = None):
    """Update voice configuration for a session (Stage 5)"""
    if session_id not in _voice_config_map:
        _voice_config_map[session_id] = VoiceOptimizationConfig(preset=preset or "balanced")
    
    config = _voice_config_map[session_id]
    
    if preset:
        config.set_preset(preset)
    else:
        config.set_silence_timeout(silence_timeout_ms)
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "message": "Voice configuration updated",
        "voice_config": config.get_config(),
    }


@app.get("/cost-tracking")
def get_cost_tracking(session_id: str, user_id: str):
    """Get cost tracking information for a session"""
    cost_info = _cost_tracker.get_session_cost(session_id)
    return {
        "session_id": session_id,
        "user_id": user_id,
        "cost_tracking": cost_info,
    }


@app.post("/reset-session")
def reset_session(session_id: str, user_id: str):
    """Reset cost tracking and config for a session"""
    _cost_tracker.reset_session(session_id)
    _message_deduplicator.clear_session(session_id)
    if session_id in _voice_config_map:
        del _voice_config_map[session_id]
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "message": "Session reset successfully",
    }
