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
