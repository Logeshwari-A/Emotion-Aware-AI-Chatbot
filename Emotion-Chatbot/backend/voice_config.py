"""
Voice and utterance optimization configuration for Stage 5
Manages silence detection, deduplication, and cost tracking
"""

# Utterance finalization settings (milliseconds)
VOICE_CONFIG = {
    # Silence detection window - time to wait for silence before finalizing utterance
    "silence_timeout_ms": 1000,  # Default 1000ms, adjustable range 700-1200ms
    "min_silence_ms": 700,       # Minimum silence detection window
    "max_silence_ms": 1200,      # Maximum silence detection window
    
    # Utterance length limits (milliseconds)
    "max_utterance_duration_ms": 12000,  # 12 seconds max per utterance
    "min_utterance_duration_ms": 800,    # 0.8 seconds min (prevent accidental sends)
    
    # Deduplication settings
    "enable_deduplication": True,
    "dedup_time_window_ms": 2000,  # Consider messages within 2s as potential duplicates
    "dedup_similarity_threshold": 0.85,  # 85% similarity needed to consider as duplicate
    
    # Cost tracking (API calls per session/user)
    "enable_cost_tracking": True,
    "cost_per_utterance_units": 1.0,  # Cost units per API call
    "cost_per_token_units": 0.001,    # Micro-cost per token
    "max_cost_per_session": 100.0,    # Max cost units per session before throttling
    "warning_cost_threshold": 75.0,   # Warn user at 75% of limit
    
    # Throttling settings
    "enable_throttling": True,
    "min_time_between_utterances_ms": 500,  # Min 500ms between messages
    "throttle_messages": [
        "API rate limit approaching. Please pause for a moment.",
        "Cost limit reached. Voice input paused.",
    ],
}

# Presets for different optimization modes
VOICE_PRESETS = {
    "conservative": {
        # Slower, more accurate
        "silence_timeout_ms": 1200,
        "min_utterance_duration_ms": 1000,
        "enable_deduplication": True,
        "dedup_similarity_threshold": 0.9,
    },
    "balanced": {
        # Default - good balance
        "silence_timeout_ms": 1000,
        "min_utterance_duration_ms": 800,
        "enable_deduplication": True,
        "dedup_similarity_threshold": 0.85,
    },
    "aggressive": {
        # Faster, more responsive
        "silence_timeout_ms": 700,
        "min_utterance_duration_ms": 600,
        "enable_deduplication": True,
        "dedup_similarity_threshold": 0.75,
    },
    "cost_conscious": {
        # Minimizes API calls
        "silence_timeout_ms": 1200,
        "min_utterance_duration_ms": 1200,
        "enable_deduplication": True,
        "dedup_similarity_threshold": 0.95,
        "max_cost_per_session": 50.0,
    },
}

class VoiceOptimizationConfig:
    """
    Runtime configuration for voice optimization settings
    Allows per-session customization
    """
    
    def __init__(self, preset="balanced"):
        """Initialize with a preset or custom config"""
        self.config = VOICE_CONFIG.copy()
        if preset in VOICE_PRESETS:
            self.config.update(VOICE_PRESETS[preset])
    
    def set_silence_timeout(self, ms):
        """Set silence timeout, enforcing min/max bounds"""
        ms = max(self.config["min_silence_ms"], min(ms, self.config["max_silence_ms"]))
        self.config["silence_timeout_ms"] = ms
        return ms
    
    def get_silence_timeout(self):
        """Get current silence timeout"""
        return self.config["silence_timeout_ms"]
    
    def set_preset(self, preset_name):
        """Switch to a preset configuration"""
        if preset_name in VOICE_PRESETS:
            self.config.update(VOICE_PRESETS[preset_name])
            return True
        return False
    
    def get_config(self):
        """Get current full configuration"""
        return self.config.copy()
    
    def to_dict(self):
        """Export config as dictionary"""
        return self.config
