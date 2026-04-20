"""
Message deduplication and cost tracking utilities for Stage 5
"""

import hashlib
import time
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional


class MessageDeduplicator:
    """
    Detects and prevents duplicate messages from being processed
    Tracks message history per session with configurable time window
    """
    
    def __init__(self, time_window_ms: int = 2000, similarity_threshold: float = 0.85):
        """
        Args:
            time_window_ms: Time window for considering duplicates (default 2000ms)
            similarity_threshold: Similarity score required to flag as duplicate (0-1)
        """
        self.time_window_ms = time_window_ms
        self.similarity_threshold = similarity_threshold
        self.message_history: Dict[str, List[Tuple[str, float, float]]] = {}  # session_id -> [(text, timestamp, hash)]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, strip whitespace)"""
        return text.lower().strip()
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)"""
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        matcher = SequenceMatcher(None, norm1, norm2)
        return matcher.ratio()
    
    def _hash_text(self, text: str) -> float:
        """Create hash of normalized text"""
        norm = self._normalize_text(text)
        return float(int(hashlib.md5(norm.encode()).hexdigest(), 16) % 10000000)
    
    def is_duplicate(self, session_id: str, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if message is a duplicate of recent messages
        
        Args:
            session_id: Session identifier
            text: Message text to check
        
        Returns:
            (is_duplicate: bool, reason: str or None)
        """
        if session_id not in self.message_history:
            self.message_history[session_id] = []
        
        current_time = time.time() * 1000  # Convert to milliseconds
        history = self.message_history[session_id]
        
        # Clean old messages outside time window
        history[:] = [
            (msg_text, timestamp, msg_hash)
            for msg_text, timestamp, msg_hash in history
            if (current_time - timestamp) <= self.time_window_ms
        ]
        
        # Check against recent messages
        for prev_text, prev_timestamp, prev_hash in history:
            similarity = self._text_similarity(text, prev_text)
            time_diff = current_time - prev_timestamp
            
            if similarity >= self.similarity_threshold and time_diff < 1000:
                # High similarity + very recent = likely duplicate
                return True, f"Duplicate detected (similarity: {similarity:.0%}, within {time_diff:.0f}ms)"
        
        # Not a duplicate, add to history
        text_hash = self._hash_text(text)
        history.append((text, current_time, text_hash))
        
        return False, None
    
    def clear_session(self, session_id: str):
        """Clear message history for a session"""
        if session_id in self.message_history:
            del self.message_history[session_id]


class CostTracker:
    """
    Tracks API usage and costs per session/user
    Enforces cost limits and provides throttling feedback
    """
    
    def __init__(self, max_cost_per_session: float = 100.0, 
                 cost_per_utterance: float = 1.0, 
                 cost_per_token: float = 0.001):
        """
        Args:
            max_cost_per_session: Maximum cost units per session
            cost_per_utterance: Cost of one utterance/API call
            cost_per_token: Micro-cost per token in response
        """
        self.max_cost_per_session = max_cost_per_session
        self.cost_per_utterance = cost_per_utterance
        self.cost_per_token = cost_per_token
        self.session_costs: Dict[str, float] = {}
        self.utterance_counts: Dict[str, int] = {}
        self.session_start_times: Dict[str, float] = {}
    
    def start_session(self, session_id: str):
        """Initialize cost tracking for a session"""
        self.session_costs[session_id] = 0.0
        self.utterance_counts[session_id] = 0
        self.session_start_times[session_id] = time.time()
    
    def add_utterance_cost(self, session_id: str, response_tokens: int = 0) -> Tuple[float, float, bool]:
        """
        Record an utterance and calculate cost
        
        Args:
            session_id: Session identifier
            response_tokens: Number of tokens in response (for fine-grained cost)
        
        Returns:
            (current_cost, cost_limit, is_over_limit: bool)
        """
        if session_id not in self.session_costs:
            self.start_session(session_id)
        
        # Calculate cost for this utterance
        utterance_cost = self.cost_per_utterance
        token_cost = response_tokens * self.cost_per_token
        total_cost = utterance_cost + token_cost
        
        self.session_costs[session_id] += total_cost
        self.utterance_counts[session_id] += 1
        
        current_cost = self.session_costs[session_id]
        is_over_limit = current_cost > self.max_cost_per_session
        
        return current_cost, self.max_cost_per_session, is_over_limit
    
    def get_session_cost(self, session_id: str) -> Dict:
        """Get cost information for a session"""
        if session_id not in self.session_costs:
            self.start_session(session_id)
        
        current_cost = self.session_costs[session_id]
        max_cost = self.max_cost_per_session
        usage_percent = (current_cost / max_cost * 100) if max_cost > 0 else 0
        utterance_count = self.utterance_counts.get(session_id, 0)
        
        return {
            "current_cost": current_cost,
            "max_cost": max_cost,
            "usage_percent": usage_percent,
            "utterance_count": utterance_count,
            "is_over_limit": current_cost > max_cost,
        }
    
    def reset_session(self, session_id: str):
        """Reset cost tracking for a session"""
        if session_id in self.session_costs:
            del self.session_costs[session_id]
        if session_id in self.utterance_counts:
            del self.utterance_counts[session_id]
        if session_id in self.session_start_times:
            del self.session_start_times[session_id]
    
    def get_remaining_budget(self, session_id: str) -> float:
        """Get remaining cost budget for session"""
        if session_id not in self.session_costs:
            return self.max_cost_per_session
        return max(0.0, self.max_cost_per_session - self.session_costs[session_id])


class ThrottleManager:
    """
    Manages request throttling to prevent API overload
    Tracks timing and enforces minimum intervals between requests
    """
    
    def __init__(self, min_interval_ms: int = 500):
        """
        Args:
            min_interval_ms: Minimum milliseconds between requests
        """
        self.min_interval_ms = min_interval_ms
        self.last_request_time: Dict[str, float] = {}
    
    def should_throttle(self, session_id: str) -> Tuple[bool, float]:
        """
        Check if request should be throttled
        
        Args:
            session_id: Session identifier
        
        Returns:
            (should_throttle: bool, wait_ms: float)
        """
        current_time = time.time() * 1000
        
        if session_id not in self.last_request_time:
            self.last_request_time[session_id] = current_time
            return False, 0.0
        
        time_since_last = current_time - self.last_request_time[session_id]
        
        if time_since_last < self.min_interval_ms:
            wait_ms = self.min_interval_ms - time_since_last
            return True, wait_ms
        
        self.last_request_time[session_id] = current_time
        return False, 0.0
    
    def mark_request(self, session_id: str):
        """Mark that a request was made"""
        self.last_request_time[session_id] = time.time() * 1000
