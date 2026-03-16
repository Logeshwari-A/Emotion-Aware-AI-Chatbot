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
