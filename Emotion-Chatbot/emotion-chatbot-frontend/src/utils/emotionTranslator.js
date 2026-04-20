/**
 * Translate detected emotion + confidence into human-friendly language.
 * Used by Magic Mirror panel to explain the assistant's internal state.
 */

export function translateEmotionToHuman(emotion, confidence) {
  if (!emotion || confidence == null) {
    return "I'm not picking up a clear emotional signal right now.";
  }

  const conf = parseFloat(confidence) || 0;
  let intensity = "";

  // Map confidence to intensity descriptor.
  if (conf >= 0.9) {
    intensity = "very ";
  } else if (conf >= 0.75) {
    intensity = "";
  } else if (conf >= 0.6) {
    intensity = "somewhat ";
  } else {
    return "I'm picking up mixed signals from what you're sharing.";
  }

  const translations = {
    sadness: `You seem ${intensity}sad right now.`,
    joy: `You seem ${intensity}happy and positive right now.`,
    anger: `You seem ${intensity}frustrated or upset right now.`,
    fear: `You seem ${intensity}anxious or worried right now.`,
    surprise: `You seem ${intensity}caught off-guard right now.`,
    disgust: `You seem ${intensity}uncomfortable with something.`,
    neutral: "I'm not picking up strong emotions right now.",
  };

  return translations[emotion] || `You seem to be experiencing ${emotion}.`;
}

/**
 * Translate strategy name into human-friendly guidance.
 */
export function translateStrategyToHuman(strategy) {
  const strategies = {
    normal_mode:
      "I'll respond in a straightforward, supportive way.",
    comfort_mode:
      "I can tell you might be going through something—I'm here to listen and support you.",
    calm_down_mode:
      "I notice some frustration. Let's take a breath and talk this through calmly.",
    motivation_mode:
      "I can feel your positive energy! Let's celebrate what's going well.",
    deep_support_mode:
      "I sense you've been carrying something heavy. I want to help you work through it.",
    advice_mode:
      "Based on what you're sharing, I have some practical thoughts that might help.",
    crisis_override:
      "Your safety matters most right now. I'm here to help you get immediate support.",
    rate_limited:
      "I'm here to help—let's slow down a moment and take time between messages.",
  };

  return strategies[strategy] || "I'm ready to listen and help.";
}

/**
 * Translate risk level into human-friendly warning.
 */
export function translateRiskToHuman(riskLevel) {
  const risks = {
    low: null,
    medium: "I'm noticing some emotional intensity here—let's talk about it together.",
    high: "Your safety is my top priority right now. I'm here to help you get support.",
  };

  return risks[riskLevel] || null;
}

/**
 * Build a summary of the reasoning path in plain language.
 */
export function buildReasoningPathHuman(reasoningPath) {
  if (!reasoningPath) return null;

  const parts = [];
  const { emotional_signal, strategy_selected, safety_override } = reasoningPath;

  if (emotional_signal) {
    parts.push(`Emotional signal: ${emotional_signal}`);
  }
  if (strategy_selected) {
    parts.push(`Strategy: ${strategy_selected}`);
  }
  if (safety_override === "Yes") {
    parts.push("Safety override active");
  }

  return parts.length > 0 ? parts.join(" • ") : null;
}
