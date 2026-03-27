from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from models.emotion_model import detect_emotion
from database import init_db, save_conversation, get_last_conversations
from database import generate_long_term_summary
from database import get_emotion_trend
from agents.trend_analyzer import analyze_emotional_trend
from agents.strategy_controller import select_strategy
from agents.prompt_builder import build_strategy_instruction
from groq import Groq
import os
from dotenv import load_dotenv

# Load API key directly from .env file
from pathlib import Path
env_path = Path(__file__).parent / '.env'

# Try loading with dotenv first
load_dotenv(dotenv_path=str(env_path))
api_key = os.getenv("GROQ_API_KEY")

# If dotenv didn't work, read directly
if not api_key or api_key == "your-real-api-key-here":
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GROQ_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    print(f"[SUCCESS] ✅ Groq API key loaded directly from file: {api_key[:15]}...")
                    break
    except Exception as e:
        print(f"[ERROR] Could not read .env file: {e}")

if not api_key or api_key == "your-real-api-key-here":
    print("[ERROR] ❌ Groq API key is missing or invalid! Check your .env file.")
    print(f"[ERROR] Looking for .env at: {env_path}")

client = Groq(api_key=api_key)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

def generate_llm_response(user_message, strategy, instruction):
    """Generate contextual response using Groq based on strategy and emotion."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an empathetic AI chatbot assistant.\n\nStrategy: {instruction}\n\nRespond in 1-2 sentences, keeping responses natural, warm, and conversational."
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print(f"❌ Groq API FAILED!")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        traceback.print_exc()
        print("="*60 + "\n")
        # Fallback to simple response if LLM fails
        return f"I hear you. Tell me more about what you're feeling."

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

    # 1) Detect emotion with a safe fallback to avoid request failures.
    try:
        emotion_data = detect_emotion(user_message)
        emotion = emotion_data.get("emotion", "neutral")
        confidence = emotion_data.get("confidence", 0.0)
    except Exception:
        emotion = "neutral"
        confidence = 0.0

    # 2) Save USER message. Continue even if persistence has a transient issue.
    try:
        save_conversation(
            user_id=user_id,
            role="user",
            message=user_message,
            emotion=emotion,
            confidence=confidence
        )
    except Exception:
        pass

    # 3) Retrieve memory and analytics with resilient fallbacks.
    try:
        past_conversations = get_last_conversations(user_id, limit=5)
    except Exception:
        past_conversations = []

    try:
        emotion_trend = get_emotion_trend(user_id)
    except Exception:
        emotion_trend = {"trend": "no_data"}

    try:
        long_term_summary = generate_long_term_summary(user_id)
    except Exception:
        long_term_summary = "No long-term emotional data yet."

    # Emotion confidence filter
    if confidence is not None and confidence < 0.6:
      emotion = "neutral"

    # 4) Agentic decision layer with robust defaults.
    try:
        trend_data = analyze_emotional_trend(user_id, limit=10)
    except Exception:
        trend_data = {
            "dominant_emotion": None,
            "trend_score": 0.0,
            "emotion_counts": {}
        }

    try:
        strategy = select_strategy(emotion, confidence, trend_data)
    except Exception:
        strategy = "normal_mode"

    try:
        instruction = build_strategy_instruction(strategy)
    except Exception:
        instruction = "Respond supportively and neutrally; ask clarifying questions when appropriate."

    # 5) Enhanced rule-based response generator with variety
    import random
    lower_message = user_message.lower()

    def generate_response(strategy, emotion, message_text):
        """Generate contextual, varied responses based on strategy and emotion"""
        
        # Greeting responses
        if "how are you" in message_text:
            greetings = [
                "I'm doing well, thank you for asking! How are you feeling?",
                "I appreciate you asking! I'm here and ready to listen. How are things with you?",
                "Thanks for checking in! Tell me, what's on your mind today?"
            ]
            return random.choice(greetings)
        
        if "hello" in message_text or "hi" in message_text or "hey" in message_text:
            hellos = [
                "Hello! I'm here to listen. What's on your mind?",
                "Hey there! How are you feeling today?",
                "Hi! Great to chat with you. What would you like to talk about?"
            ]
            return random.choice(hellos)
        
        # Strategy-specific responses
        if strategy == "comfort_mode":
            comfort_responses = [
                "I hear you. It sounds like you're going through something difficult. I'm here to listen.",
                "That sounds really tough. I'm here for you. Would you like to share more?",
                "I can sense something is weighing on you. You're not alone—I'm here to help.",
                "It's okay to feel this way. I'm here to support you. Tell me more about what you're feeling.",
                "I'm listening and I care about what you're experiencing. Let's talk through this together."
            ]
            return random.choice(comfort_responses)
        
        if strategy == "calm_down_mode":
            calm_responses = [
                "I can sense there's some frustration here. Let's take a breath together and talk through it.",
                "It sounds like something upset you. Let's take a moment and discuss what happened.",
                "I understand you're feeling upset. Breathing deeply can help—want to talk about what triggered this?",
                "Let's pause and focus. I'm here to help you work through this anger constructively."
            ]
            return random.choice(calm_responses)
        
        if strategy == "motivation_mode":
            motivation_responses = [
                "That's wonderful! I can feel the positivity. Tell me more about what made you feel this way!",
                "That's amazing news! What's been going well for you?",
                "I love your energy! What accomplishment are you celebrating?",
                "That sounds fantastic! What happened that made your day so great?"
            ]
            return random.choice(motivation_responses)
        
        if strategy == "deep_support_mode":
            deep_responses = [
                "I've noticed you've been carrying a lot of sadness lately. How can I best support you right now?",
                "It seems like you've been struggling for a while. I want you to know you don't have to face this alone.",
                "I can see that this has been a challenging period for you. Let's work through this together.",
                "Your well-being matters to me. I'm here to provide the support you need."
            ]
            return random.choice(deep_responses)
        
        # Emotion-specific responses for normal_mode
        if strategy == "normal_mode":
            if emotion == "sadness":
                sad_responses = [
                    "I sense some sadness in what you're saying. What's been troubling you?",
                    "It sounds like you're feeling down. Want to talk about what's happening?",
                    "I hear sadness in your words. I'm here to listen and support you."
                ]
                return random.choice(sad_responses)
            
            if emotion == "joy":
                joy_responses = [
                    "That sounds wonderful! What made you feel so happy?",
                    "I can feel the joy in your words! Tell me more about this positive experience.",
                    "That's amazing! What's brought so much happiness into your day?"
                ]
                return random.choice(joy_responses)
            
            if emotion == "anger":
                anger_responses = [
                    "It sounds like something frustrated you. What happened?",
                    "I can sense some irritation. Want to talk about what upset you?",
                    "It seems something didn't go as planned. Let's discuss it."
                ]
                return random.choice(anger_responses)
            
            if emotion == "fear":
                fear_responses = [
                    "I understand that anxiety can feel overwhelming. What's worrying you?",
                    "It sounds like something's concerning you. I'm here to help you work through it.",
                    "Fear is a natural emotion. What specifically is troubling you right now?"
                ]
                return random.choice(fear_responses)
            
            # Default normal mode
            normal_responses = [
                "Tell me more about what's on your mind.",
                "I'm listening. What would you like to share?",
                "What's happening that you'd like to talk about?",
                "I'm here to listen. Go ahead, I'm all ears.",
                "What's been going on with you lately?"
            ]
            return random.choice(normal_responses)
        
        # Fallback
        fallback = [
            "I'm here to listen and support you.",
            "Tell me more, I'm here for you.",
            "What's on your mind? I'm listening.",
            "I'm here to help. What can we talk about?"
        ]
        return random.choice(fallback)
    
    # Use LLM to generate response
    response_text = generate_llm_response(user_message, strategy, instruction)

    # 6) Save ASSISTANT response.
    try:
        save_conversation(
            user_id=user_id,
            role="assistant",
            message=response_text
        )
    except Exception:
        pass
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
