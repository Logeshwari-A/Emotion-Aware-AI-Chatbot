"""
Tests for Stage 5 API optimization features
- Message deduplication
- Cost tracking
- Throttling
- Voice configuration
"""

import pytest
import time
from optimization_utils import MessageDeduplicator, CostTracker, ThrottleManager
from voice_config import VoiceOptimizationConfig, VOICE_PRESETS


class TestMessageDeduplicator:
    """Test message deduplication"""
    
    def test_identical_message_is_duplicate(self):
        """Two identical messages should be flagged as duplicate"""
        dedup = MessageDeduplicator(time_window_ms=2000, similarity_threshold=0.85)
        
        session_id = "test_session_1"
        message = "I feel anxious today"
        
        is_dup1, reason1 = dedup.is_duplicate(session_id, message)
        assert not is_dup1, "First message should not be duplicate"
        
        is_dup2, reason2 = dedup.is_duplicate(session_id, message)
        assert is_dup2, "Identical second message should be duplicate"
        assert reason2 is not None
    
    def test_similar_message_is_duplicate(self):
        """Very similar messages should be flagged as duplicate"""
        dedup = MessageDeduplicator(time_window_ms=2000, similarity_threshold=0.85)
        
        session_id = "test_session_2"
        msg1 = "I feel anxious"
        msg2 = "i feel anxious"  # Different case
        
        is_dup1, _ = dedup.is_duplicate(session_id, msg1)
        assert not is_dup1
        
        is_dup2, reason2 = dedup.is_duplicate(session_id, msg2)
        assert is_dup2, "Similar message should be duplicate"
    
    def test_different_message_not_duplicate(self):
        """Different messages should not be flagged as duplicate"""
        dedup = MessageDeduplicator(time_window_ms=2000, similarity_threshold=0.85)
        
        session_id = "test_session_3"
        msg1 = "I feel anxious"
        msg2 = "I feel happy today"
        
        is_dup1, _ = dedup.is_duplicate(session_id, msg1)
        assert not is_dup1
        
        is_dup2, reason2 = dedup.is_duplicate(session_id, msg2)
        assert not is_dup2, "Different message should not be duplicate"
    
    def test_old_message_not_considered_duplicate(self):
        """Messages outside time window should not be flagged as duplicate"""
        dedup = MessageDeduplicator(time_window_ms=100, similarity_threshold=0.85)
        
        session_id = "test_session_4"
        message = "Test message"
        
        is_dup1, _ = dedup.is_duplicate(session_id, message)
        assert not is_dup1
        
        # Wait for time window to pass
        time.sleep(0.15)
        
        is_dup2, _ = dedup.is_duplicate(session_id, message)
        assert not is_dup2, "Old message outside window should not be duplicate"


class TestCostTracker:
    """Test cost tracking"""
    
    def test_cost_accumulation(self):
        """Costs should accumulate correctly"""
        tracker = CostTracker(max_cost_per_session=100.0, cost_per_utterance=1.0, cost_per_token=0.001)
        
        session_id = "cost_session_1"
        tracker.start_session(session_id)
        
        # First utterance: 1.0 + (100 tokens * 0.001) = 1.1
        current_cost, max_cost, over_limit = tracker.add_utterance_cost(session_id, response_tokens=100)
        assert current_cost == 1.1, f"Expected 1.1, got {current_cost}"
        assert not over_limit
        
        # Second utterance: 1.1 + 1.1 = 2.2
        current_cost, max_cost, over_limit = tracker.add_utterance_cost(session_id, response_tokens=100)
        assert current_cost == 2.2, f"Expected 2.2, got {current_cost}"
        assert not over_limit
    
    def test_cost_limit_exceeded(self):
        """Should detect when cost limit is exceeded"""
        tracker = CostTracker(max_cost_per_session=10.0, cost_per_utterance=5.0, cost_per_token=0.0)
        
        session_id = "cost_session_2"
        tracker.start_session(session_id)
        
        # First call: 5.0 (under limit)
        _, _, over_limit = tracker.add_utterance_cost(session_id, response_tokens=0)
        assert not over_limit
        
        # Second call: 5.0 + 5.0 = 10.0 (at limit)
        _, _, over_limit = tracker.add_utterance_cost(session_id, response_tokens=0)
        assert not over_limit
        
        # Third call: 10.0 + 5.0 = 15.0 (exceeds limit)
        _, _, over_limit = tracker.add_utterance_cost(session_id, response_tokens=0)
        assert over_limit, "Should exceed cost limit"
    
    def test_get_session_cost(self):
        """Should retrieve session cost info"""
        tracker = CostTracker(max_cost_per_session=100.0, cost_per_utterance=1.0, cost_per_token=0.0)
        
        session_id = "cost_session_3"
        tracker.start_session(session_id)
        tracker.add_utterance_cost(session_id, response_tokens=0)
        
        cost_info = tracker.get_session_cost(session_id)
        assert cost_info["current_cost"] == 1.0
        assert cost_info["max_cost"] == 100.0
        assert cost_info["usage_percent"] == 1.0
        assert cost_info["utterance_count"] == 1


class TestThrottleManager:
    """Test throttling"""
    
    def test_throttle_when_interval_too_short(self):
        """Should throttle when requests are too close"""
        throttle = ThrottleManager(min_interval_ms=100)
        
        session_id = "throttle_session_1"
        
        # First request - should not throttle
        should_throttle1, wait_ms1 = throttle.should_throttle(session_id)
        assert not should_throttle1
        
        # Immediate second request - should throttle
        should_throttle2, wait_ms2 = throttle.should_throttle(session_id)
        assert should_throttle2, "Second immediate request should be throttled"
        assert wait_ms2 > 0, "Wait time should be positive"
    
    def test_no_throttle_after_interval(self):
        """Should not throttle after sufficient interval"""
        throttle = ThrottleManager(min_interval_ms=50)
        
        session_id = "throttle_session_2"
        
        should_throttle1, _ = throttle.should_throttle(session_id)
        assert not should_throttle1
        
        # Wait for interval
        time.sleep(0.1)
        
        should_throttle2, _ = throttle.should_throttle(session_id)
        assert not should_throttle2, "Should not throttle after waiting"


class TestVoiceOptimizationConfig:
    """Test voice optimization configuration"""
    
    def test_default_config_balanced(self):
        """Default config should be 'balanced'"""
        config = VoiceOptimizationConfig(preset="balanced")
        
        assert config.get_silence_timeout() == 1000
    
    def test_preset_conservative(self):
        """Conservative preset should have longer timeout"""
        config = VoiceOptimizationConfig(preset="conservative")
        
        assert config.get_silence_timeout() == 1200
    
    def test_preset_aggressive(self):
        """Aggressive preset should have shorter timeout"""
        config = VoiceOptimizationConfig(preset="aggressive")
        
        assert config.get_silence_timeout() == 700
    
    def test_silence_timeout_bounds(self):
        """Silence timeout should be bounded"""
        config = VoiceOptimizationConfig()
        
        # Try to set below minimum
        result = config.set_silence_timeout(500)
        assert result == 700, "Should be bounded to minimum"
        
        # Try to set above maximum
        result = config.set_silence_timeout(1500)
        assert result == 1200, "Should be bounded to maximum"
    
    def test_get_config(self):
        """Should return full config dict"""
        config = VoiceOptimizationConfig(preset="balanced")
        full_config = config.get_config()
        
        assert "silence_timeout_ms" in full_config
        assert "enable_deduplication" in full_config
        assert "enable_cost_tracking" in full_config


if __name__ == "__main__":
    # Run tests: pytest test_stage5.py -v
    pytest.main([__file__, "-v"])
