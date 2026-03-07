from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from models.emotion_model import detect_emotion
from database import init_db, save_conversation, get_last_conversations
from database import generate_long_term_summary
from database import get_emotion_trend
from backend.agents.trend_analyzer import analyze_emotional_trend
from backend.agents.strategy_controller import select_strategy
from backend.agents.prompt_builder import build_strategy_instruction
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

def generate_llm_response(*args, **kwargs):
    # LLM integration is currently paused. This function is a placeholder.
    raise RuntimeError("LLM integration is paused. Do not call generate_llm_response()")

class ChatRequest(BaseModel):
    message: str
    user_id: str

@app.get("/")
def home():
    return {"message": "Emotion Chatbot Backend Running"}

@app.post("/chat")
def chat(request: ChatRequest):

    user_message = request.message
    user_id = request.user_id

    # 1️⃣ Detect emotion
    emotion_data = detect_emotion(user_message)
    emotion = emotion_data["emotion"]
    confidence = emotion_data["confidence"]

    # 2️⃣ Save USER message
    save_conversation(
        user_id=user_id,
        role="user",
        message=user_message,
        emotion=emotion,
        confidence=confidence
    )

    # 3️⃣ Retrieve sliding window memory
    past_conversations = get_last_conversations(user_id, limit=5)
    
    #  Emotion trend analysis
    emotion_trend = get_emotion_trend(user_id)

    #  Long-term summary
    long_term_summary = generate_long_term_summary(user_id)

    # Emotion confidence filter
    if confidence is not None and confidence < 0.6:
      emotion = "neutral"

    # 4️⃣ Agentic Decision Layer: analyze trend, choose strategy, build instruction
    trend_data = analyze_emotional_trend(user_id, limit=10)
    strategy = select_strategy(emotion, confidence, trend_data)
    instruction = build_strategy_instruction(strategy)

    # 5️⃣ Temporary rule-based response generator (LLM paused)
    lower_message = user_message.lower()

    if strategy == "normal_mode":
        if "how are you" in lower_message:
            response_text = "I'm doing well. Thank you for asking! How are you feeling today?"
        elif "hello" in lower_message or "hi" in lower_message:
            response_text = "Hello! I'm here to listen. How are you feeling today?"
        elif emotion == "sadness":
            response_text = "I can sense some sadness. Would you like to share what's troubling you?"
        elif emotion == "joy":
            response_text = "That sounds wonderful! What made you feel so positive?"
        elif emotion == "anger":
            response_text = "It seems something upset you. Do you want to talk about it?"
        elif emotion == "fear":
            response_text = "I understand that feeling worried can be difficult. What is causing this fear?"
        else:
            response_text = "Tell me more about what's on your mind."
    elif strategy == "comfort_mode":
        response_text = "I'm here for you. Do you want to talk about what's making you feel this way?"
    elif strategy == "calm_down_mode":
        response_text = "Let's take a moment to breathe. What happened that made you feel angry?"
    elif strategy == "motivation_mode":
        response_text = "That's great to hear! Tell me more about it."
    elif strategy == "deep_support_mode":
        response_text = "It seems you've been feeling down for a while. I'm here to listen."
    else:
        response_text = "I'm listening. Tell me more."

    # 5️⃣ Save ASSISTANT response
    save_conversation(
        user_id=user_id,
        role="assistant",
        message=response_text
    )
    return {
        "user_id": user_id,
        "detected_emotion": emotion,
        "confidence": confidence,
        "strategy": strategy,
        "trend_analysis": trend_data,
        "recent_memory": past_conversations,
        "emotion_trend": emotion_trend,
        "long_term_summary": long_term_summary,
        "instruction": instruction,
        "response": response_text,
    }