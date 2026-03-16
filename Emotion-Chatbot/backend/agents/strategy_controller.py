def select_strategy(emotion, confidence, trend_data):
    """Select conversational strategy based on emotion, confidence, and trend analysis."""
    dominant = trend_data.get("dominant_emotion")
    trend_score = trend_data.get("trend_score", 0.0)

    if emotion == "sadness" and confidence is not None and confidence > 0.75:
        return "comfort_mode"

    if emotion == "anger":
        return "calm_down_mode"

    if dominant == "sadness" and trend_score > 0.6:
        return "deep_support_mode"

    if emotion == "joy":
        return "motivation_mode"

    return "normal_mode"
