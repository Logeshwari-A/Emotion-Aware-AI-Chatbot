import sqlite3
from collections import Counter

DB_NAME = "chat_memory.db"


def analyze_emotional_trend(user_id, limit=10, db_name=DB_NAME):
    """Retrieve last `limit` user emotions and compute distribution, dominant emotion, and trend score."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT emotion
        FROM conversations
        WHERE user_id = ?
        AND role = 'user'
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    emotions = [r[0] for r in rows if r[0] is not None]

    if not emotions:
        return {
            "dominant_emotion": None,
            "trend_score": 0.0,
            "emotion_counts": {}
        }

    counts = Counter(emotions)
    dominant = counts.most_common(1)[0][0]
    total = sum(counts.values())
    trend_score = counts[dominant] / total if total > 0 else 0.0

    return {
        "dominant_emotion": dominant,
        "trend_score": round(trend_score, 3),
        "emotion_counts": dict(counts)
    }


def select_strategy(current_emotion, confidence, trend_data):
    """Decide a conversational strategy based on current emotion, confidence, and trend info."""
    dominant = trend_data.get("dominant_emotion")
    trend_score = trend_data.get("trend_score", 0.0)

    # High-confidence sadness → comforting
    if current_emotion == "sadness" and confidence is not None and confidence > 0.75:
        return "comfort_mode"

    # Anger → de-escalation
    if current_emotion == "anger":
        return "calm_down_mode"

    # Persistent sadness trend → deep support
    if dominant == "sadness" and trend_score > 0.6:
        return "deep_support_mode"

    # Joyous → motivation
    if current_emotion == "joy":
        return "motivation_mode"

    # Fearful → advice-oriented
    if current_emotion == "fear":
        return "advice_mode"

    # Fallback to normal
    return "normal_mode"


def build_strategy_prompt(strategy):
    """Map a strategy to an LLM instruction prompt (concise)."""
    mapping = {
        "comfort_mode": (
            "Respond with empathy and emotional validation. Acknowledge feelings, offer comfort, "
            "and ask gentle follow-up questions to let the user share more. Keep tone warm and supportive."
        ),
        "advice_mode": (
            "Provide structured, practical suggestions to manage stress and fear. Offer clear steps, "
            "safety tips, and optional resources. Keep tone calm and actionable."
        ),
        "motivation_mode": (
            "Respond with positive reinforcement and encouragement. Celebrate progress and suggest "
            "small next steps to build momentum. Keep tone upbeat."
        ),
        "calm_down_mode": (
            "Use de-escalation techniques: normalize the emotion, offer grounding exercises, and "
            "encourage slow breathing. Keep language soothing and non-judgmental."
        ),
        "normal_mode": (
            "Respond in a supportive, neutral manner. Ask clarifying questions when helpful and "
            "invite further sharing."
        ),
        "deep_support_mode": (
            "Offer deeper supportive dialogue: validate persistent sadness, gently explore causes, "
            "suggest coping strategies and, when appropriate, recommend seeking professional support."
        )
    }

    return mapping.get(strategy, mapping["normal_mode"])
