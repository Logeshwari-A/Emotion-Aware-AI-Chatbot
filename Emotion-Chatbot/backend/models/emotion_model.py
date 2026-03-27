from transformers import pipeline

emotion_classifier = None

def get_emotion_classifier():
    global emotion_classifier
    if emotion_classifier is None:
        emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base"
        )
    return emotion_classifier

def detect_emotion(text):
    classifier = get_emotion_classifier()
    results = classifier(text)

    # Since model already returns top emotion
    top_emotion = results[0]

    return {
        "emotion": top_emotion["label"],
        "confidence": round(top_emotion["score"], 3)
    }