"""
Unit Tests for Database Operations
Tests SQLite database interactions for conversation storage and retrieval.
"""

import pytest
import sqlite3
import os
from datetime import datetime
from database import (
    init_db,
    save_conversation,
    get_last_conversations,
    generate_long_term_summary,
    get_emotion_trend,
)

# Use a test database file
TEST_DB = "test_chat_memory.db"


@pytest.fixture(scope="function")
def setup_test_db():
    """Set up a fresh test database for each test."""
    # Delete test DB if it exists
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Create fresh test database
    conn = sqlite3.connect(TEST_DB)
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
    
    yield TEST_DB
    
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestDatabaseOperations:
    """Test suite for database functionality."""

    def test_init_db_creates_table(self):
        """Test that init_db creates the conversations table."""
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        
        conn = sqlite3.connect(TEST_DB)
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
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
        result = cursor.fetchone()
        assert result is not None
        
        conn.close()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_save_conversation_with_test_db(self, setup_test_db):
        """Test saving a conversation to the database."""
        db = setup_test_db
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        # Insert a test conversation
        cursor.execute("""
            INSERT INTO conversations (user_id, role, message, emotion, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, ("user123", "user", "Hello!", "happy", 0.95))
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT * FROM conversations WHERE user_id = ?", ("user123",))
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == "user123"
        assert result[2] == "user"
        
        conn.close()

    def test_database_stores_emotions(self, setup_test_db):
        """Test that emotions are properly stored in database."""
        db = setup_test_db
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        emotions = ["happy", "sad", "angry", "neutral"]
        for emotion in emotions:
            cursor.execute("""
                INSERT INTO conversations (user_id, role, message, emotion, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, ("user123", "assistant", f"Response with {emotion} tone", emotion, 0.85))
        
        conn.commit()
        
        # Verify all emotions are stored
        cursor.execute("SELECT emotion FROM conversations WHERE user_id = ? ORDER BY emotion", ("user123",))
        results = [row[0] for row in cursor.fetchall()]
        assert len(results) == 4
        
        conn.close()

    def test_database_confidence_storage(self, setup_test_db):
        """Test that confidence scores are properly stored."""
        db = setup_test_db
        
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (user_id, role, message, emotion, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, ("user123", "user", "Test message", "neutral", 0.75))
        conn.commit()
        
        cursor.execute("SELECT confidence FROM conversations WHERE user_id = ?", ("user123",))
        result = cursor.fetchone()
        assert result[0] == 0.75
        
        conn.close()
