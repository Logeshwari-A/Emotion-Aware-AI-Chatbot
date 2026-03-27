"""
Unit Tests for Emotion Detection Model
Tests the emotion detection pipeline from HuggingFace transformers.
"""

import pytest
from models.emotion_model import detect_emotion, get_emotion_classifier


class TestEmotionDetection:
    """Test suite for emotion detection functionality."""

    def test_emotion_classifier_initialization(self):
        """Test that emotion classifier initializes correctly."""
        classifier = get_emotion_classifier()
        assert classifier is not None
        assert hasattr(classifier, '__call__')

    def test_detect_emotion_happy_text(self):
        """Test emotion detection for happy/positive text."""
        result = detect_emotion("I'm so happy and excited about this!")
        assert result is not None
        assert 'emotion' in result
        assert 'confidence' in result
        assert result['confidence'] > 0

    def test_detect_emotion_sad_text(self):
        """Test emotion detection for sad/negative text."""
        result = detect_emotion("I'm feeling really sad and depressed.")
        assert result is not None
        assert 'emotion' in result
        assert 'confidence' in result

    def test_detect_emotion_neutral_text(self):
        """Test emotion detection for neutral text."""
        result = detect_emotion("The weather is cloudy today.")
        assert result is not None
        assert 'emotion' in result
        assert 'confidence' in result

    def test_detect_emotion_angry_text(self):
        """Test emotion detection for angry text."""
        result = detect_emotion("I'm furious about this situation!")
        assert result is not None
        assert 'emotion' in result
        assert result['confidence'] >= 0

    def test_detect_emotion_returns_dict(self):
        """Test that detect_emotion returns a dictionary with required keys."""
        result = detect_emotion("This is a test message.")
        assert isinstance(result, dict)
        assert 'emotion' in result
        assert 'confidence' in result

    def test_detect_emotion_confidence_in_range(self):
        """Test that confidence score is between 0 and 1."""
        result = detect_emotion("Testing confidence scores.")
        assert 0 <= result['confidence'] <= 1

    def test_detect_emotion_empty_string(self):
        """Test emotion detection with empty string."""
        # Should handle empty string gracefully
        result = detect_emotion("")
        assert result is not None
        assert 'emotion' in result

    def test_emotion_classifier_singleton(self):
        """Test that classifier is reused (singleton pattern)."""
        classifier1 = get_emotion_classifier()
        classifier2 = get_emotion_classifier()
        # Should be the same instance
        assert classifier1 is classifier2
