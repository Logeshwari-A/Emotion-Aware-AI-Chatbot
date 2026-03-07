import sqlite3

DB_NAME = "chat_memory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            message TEXT,
            emotion TEXT,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_conversation(user_id, role, message, emotion=None, confidence=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversations (user_id, role, message, emotion, confidence)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, role, message, emotion, confidence))

    conn.commit()
    conn.close()

def get_last_conversations(user_id, limit=5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, message, emotion
        FROM conversations
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    # reverse → chronological order
    rows = rows[::-1]

    structured = [
        {
            "role": row[0],
            "message": row[1],
            "emotion": row[2]
        }
        for row in rows
    ]

    return structured

def get_emotion_trend(user_id, limit=10):
    conn = sqlite3.connect(DB_NAME)
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

    emotions = [row[0] for row in rows if row[0] is not None]

    if not emotions:
        return {"trend": "no_data"}

    # Frequency analysis
    from collections import Counter
    emotion_counts = Counter(emotions)

    dominant_emotion = emotion_counts.most_common(1)[0][0]

    return {
        "recent_emotions": emotions[::-1],
        "dominant_emotion": dominant_emotion,
        "emotion_counts": dict(emotion_counts)
    }
def generate_long_term_summary(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT emotion
        FROM conversations
        WHERE user_id = ?
        AND role = 'user'
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    emotions = [row[0] for row in rows if row[0] is not None]

    if not emotions:
        return "No long-term emotional data yet."

    from collections import Counter
    emotion_counts = Counter(emotions)
    dominant = emotion_counts.most_common(1)[0][0]

    total = len(emotions)

    summary = f"User has sent {total} messages. Most frequent emotion: {dominant}."

    return summary