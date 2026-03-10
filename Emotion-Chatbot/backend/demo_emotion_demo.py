from models.emotion_model import detect_emotion

SAMPLES = [
    "I am so happy today! The sun is shining and I feel great.",
    "I feel really sad and down.",
    "I'm furious about what happened!",
    "I'm a bit anxious about the exam tomorrow.",
]


def main():
    for text in SAMPLES:
        res = detect_emotion(text)
        print(f"Input: {text}\n→ Emotion: {res['emotion']}, Confidence: {res['confidence']}\n")


if __name__ == "__main__":
    main()
