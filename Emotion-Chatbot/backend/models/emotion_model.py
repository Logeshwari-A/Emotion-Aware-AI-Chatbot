from transformers import pipeline

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base"
)

def detect_emotion(text):
    results = emotion_classifier(text)

    # Since model already returns top emotion
    top_emotion = results[0]

    return {
        "emotion": top_emotion["label"],
        "confidence": round(top_emotion["score"], 3)
    }