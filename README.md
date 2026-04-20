# Emotion-Aware AI Chatbot

Full-stack AI chatbot project with emotion detection, adaptive response strategies, safety-aware handling, memory-backed context, and optional voice/call interaction.

## Overview

This project contains a FastAPI backend and a React + Vite frontend.

The system is designed to:
- Detect emotion from user text
- Choose an adaptive strategy based on emotional trend and confidence
- Generate supportive responses using Groq LLM
- Persist conversation context in SQLite
- Apply safety/risk overrides for harmful or crisis-like language
- Support voice input and call-style conversation UX in the frontend

## Current Capabilities

### Backend
- Emotion detection and confidence scoring
- Strategy selection (agent-based controller)
- Intent-aware short responses (friend-style, support, appreciation, story mode)
- Story start/continue flow with per-session state
- Safety gates:
  - Harmful request refusal
  - Risk-aware response style
  - Crisis override with immediate support resources
- Session protections:
  - Rate limiting
  - Duplicate message blocking
  - Throttling for rapid utterances
  - Cost tracking metadata
- Conversation memory and emotion trend summaries

### Frontend
- Chat interface with adaptive response display
- Voice mode (speech input + speech output)
- Call mode UI with transcript and controls (listen, done speaking, mute, end call)
- Voice settings panel
- Metadata panel (emotion, strategy, risk, crisis resources)
- Quick prompt starters and clear-chat controls

## Tech Stack

### Backend
- Python
- FastAPI
- Pydantic
- Transformers + Torch
- Groq Python SDK
- SQLite
- python-dotenv

### Frontend
- React 18
- Vite
- Axios
- lucide-react
- CSS

## Project Structure

```text
Emotion-Aware-AI-Chatbot/
├── README.md
├── API_TEST_RESULTS.md
├── IMPLEMENTATION_PAPER.md
├── IMPLEMENTATION_PAPER_CONTENT_ONLY.md
└── Emotion-Chatbot/
    ├── .env.example
    ├── LICENSE
    ├── requirements.txt
    ├── backend/
    │   ├── app.py
    │   ├── database.py
    │   ├── optimization_utils.py
    │   ├── voice_config.py
    │   ├── agents/
    │   │   ├── prompt_builder.py
    │   │   ├── strategy_controller.py
    │   │   └── trend_analyzer.py
    │   ├── models/
    │   │   ├── agentic.py
    │   │   └── emotion_model.py
    │   └── tests/
    │       ├── test_app.py
    │       ├── test_database.py
    │       ├── test_emotion_model.py
    │       └── test_stage5.py
    └── emotion-chatbot-frontend/
        ├── package.json
        ├── vite.config.js
        └── src/
            ├── App.jsx
            ├── main.jsx
            ├── styles.css
            ├── components/
            ├── hooks/
            ├── services/
            └── utils/
```

## Installation and Setup

## 1) Clone and enter project

```bash
git clone <your-repository-url>
cd Emotion-Aware-AI-Chatbot/Emotion-Chatbot
```

## 2) Backend setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 3) Environment setup

Create `backend/.env` and add your Groq key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

You can copy values from `Emotion-Chatbot/.env.example`.

## 4) Run backend

```bash
cd backend
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## 5) Run frontend

Open a new terminal:

```bash
cd Emotion-Aware-AI-Chatbot/Emotion-Chatbot/emotion-chatbot-frontend
npm install
npm run dev
```

## Default URLs
- Frontend: `http://localhost:5173`
- Backend: `http://127.0.0.1:8000`

## API Endpoints

### Health and chat
- `GET /` - basic backend status
- `POST /chat` - main emotion-aware chat endpoint

### Voice and session optimization
- `GET /voice-config?session_id=...&user_id=...`
- `POST /voice-config?session_id=...&user_id=...&silence_timeout_ms=1000&preset=balanced`
- `GET /cost-tracking?session_id=...&user_id=...`
- `POST /reset-session?session_id=...&user_id=...`

## `POST /chat` sample request

```json
{
  "message": "I feel stressed today",
  "user_id": "user123"
}
```

## `POST /chat` sample response (abridged)

```json
{
  "user_id": "user123",
  "session_id": "text-user123",
  "turn_id": "uuid",
  "detected_emotion": "sadness",
  "confidence": 0.89,
  "strategy": "comfort_mode",
  "intent_tag": "emotional_support",
  "risk_level": "low",
  "safety_trigger": false,
  "response": "I hear you, and I am here with you. Tell me what feels heaviest right now.",
  "cost_tracking": {
    "current_cost": 2.314,
    "max_cost": 100.0,
    "is_over_limit": false
  }
}
```

## Data Storage

SQLite table: `conversations`

Columns:
- `id` (INTEGER, PK)
- `user_id` (TEXT)
- `role` (TEXT)
- `message` (TEXT)
- `emotion` (TEXT)
- `confidence` (REAL)
- `timestamp` (DATETIME)

Current DB file used by backend code: `Emotion-Chatbot/chat_memory.db`

## Running Tests

From `Emotion-Chatbot`:

```bash
pytest backend/tests -v
```

## Notes

- Frontend API base URL is currently set in `emotion-chatbot-frontend/src/services/api.js` to `http://127.0.0.1:8000`.
- CORS is currently configured in backend to allow all origins.
- If `GROQ_API_KEY` is missing in `backend/.env`, response generation can fail.

## License

Apache License 2.0. See `Emotion-Chatbot/LICENSE`.
