# Emotion-Aware AI Chatbot – Intelligent Emotional Conversation Platform

> Final Year Project
> Full-stack system for emotion detection, adaptive response generation, and conversation memory

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Features](#features)
- [Architecture and Design](#architecture-and-design)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [API Endpoints](#api-endpoints)
- [Data Model](#data-model)
- [Configuration](#configuration)
- [Usage](#usage)
- [Advantages](#advantages)
- [Challenges Addressed](#challenges-addressed)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Emotion-Aware AI Chatbot is a full-stack web application that understands a user's emotional state from text and generates adaptive conversational responses. It combines NLP-based emotion detection, strategy-driven dialogue control, and LLM generation through Groq to provide supportive and context-aware interactions.

The platform includes a React frontend for real-time chat and a FastAPI backend that handles emotion analysis, conversation persistence, trend interpretation, and response generation.

### Key Highlights
- Real-time emotion detection from user messages
- Strategy-based response adaptation
- Conversation history and long-term summary support
- Emotional trend analysis over time
- Fast, production-ready API backend with React frontend

---

## Problem Statement

Most chatbot systems treat all user inputs equally and ignore emotional context. This leads to repetitive, tone-insensitive replies and poor user trust in emotionally sensitive conversations.

### Current Limitations in Typical Chatbots

For users:
- Lack of emotional understanding in responses
- Generic replies regardless of tone or sentiment
- No continuity across previous conversations

For systems:
- Weak adaptation to changing emotional states
- No strategy layer to handle different emotional modes
- Insufficient analytics for user emotional trends

---

## Objectives

1. Build a robust emotion-aware conversational platform.
2. Detect user emotion from text with confidence scoring.
3. Select response strategies dynamically based on emotion and trend.
4. Provide memory-aware chat using recent and long-term context.
5. Deliver a clean and responsive UI for practical usage.

---

## Features

### Core Features

- Emotion detection using transformer-based classification
- Adaptive strategy selection for response tone control
- Groq-powered LLM response generation
- Conversation persistence with SQLite
- Emotional trend and summary support
- Responsive chat interface with loading and error states

### Backend Capabilities

- REST API with FastAPI
- CORS-enabled frontend/backend communication
- Safe fallbacks for model and API failures
- Strategy instruction builder for controlled LLM prompting

### Frontend Capabilities

- Real-time chat experience
- Structured message rendering for user and assistant
- API integration with timeout/error handling
- Modern responsive layout for desktop and mobile

---

## Architecture and Design

The system follows a two-tier application architecture with a persistent local data store.

```
┌──────────────────────────────────────────────────────┐
│                FRONTEND (React + Vite)               │
│  • Chat UI                                            │
│  • Message handling and rendering                     │
│  • API client integration                             │
└───────────────────────┬──────────────────────────────┘
                        │ HTTP/REST
┌───────────────────────▼──────────────────────────────┐
│                BACKEND (FastAPI, Python)             │
│  • Emotion detection                                  │
│  • Strategy selection and prompt building             │
│  • Groq LLM response generation                       │
│  • Memory retrieval and trend analysis                │
└───────────────────────┬──────────────────────────────┘
                        │ SQLite operations
┌───────────────────────▼──────────────────────────────┐
│                   DATA LAYER (SQLite)                │
│  • Conversations table                               │
│  • Emotion and confidence persistence                │
│  • Timestamped chat history                          │
└──────────────────────────────────────────────────────┘
```

### Design Principles
- Modularity through dedicated agents and models
- Resilience through fallback handling
- Maintainability through clear separation of concerns
- User-centric interaction with emotionally aligned responses

---

## Tech Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| React 18 | Interactive UI components |
| Vite | Fast development and build tooling |
| Axios | HTTP client for backend communication |
| CSS3 | Styling and responsive layout |

### Backend
| Technology | Purpose |
|-----------|---------|
| Python | Core backend language |
| FastAPI | REST API framework |
| Pydantic | Request/response validation |
| Groq SDK | LLM inference integration |
| Transformers | Emotion classification pipeline |
| SQLite | Lightweight persistent storage |
| python-dotenv | Environment variable management |

### Development Tools
| Tool | Purpose |
|------|---------|
| Git and GitHub | Version control and collaboration |
| Pytest | Backend unit and integration testing |
| npm | Frontend package management |

---

## Project Structure

```
Emotion-Chatbot/
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── demo_emotion_demo.py
│   ├── agents/
│   │   ├── prompt_builder.py
│   │   ├── strategy_controller.py
│   │   ├── trend_analyzer.py
│   │   └── __init__.py
│   ├── models/
│   │   ├── emotion_model.py
│   │   ├── agentic.py
│   │   └── __init__.py
│   └── tests/
│       ├── test_app.py
│       ├── test_database.py
│       └── test_emotion_model.py
│
├── emotion-chatbot-frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── styles.css
│       ├── components/
│       │   ├── ChatWindow.jsx
│       │   └── MessageBubble.jsx
│       └── services/
│           └── api.js
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Installation and Setup

### Prerequisites

- Python 3.10+
- Node.js 16+
- npm
- Git
- Groq API key

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository/Emotion-Chatbot
```

### Step 2: Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r ../requirements.txt
```

### Step 3: Environment Setup

Create `backend/.env` and add:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Step 4: Run Backend

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Frontend Setup and Run

```bash
cd ../emotion-chatbot-frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`  
Backend URL: `http://127.0.0.1:8000`

---

## API Endpoints

### Active Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Backend health/info endpoint |
| POST | `/chat` | Analyze emotion and return adaptive response |

### Sample Request

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I feel stressed today",
    "user_id": "user123"
  }'
```

### Sample Response

```json
{
  "user_id": "user123",
  "detected_emotion": "sadness",
  "confidence": 0.89,
  "strategy": "comfort_mode",
  "past_conversations": [],
  "emotion_trend": {
    "trend": "no_data"
  },
  "long_term_summary": "No long-term emotional data yet.",
  "instruction": "Respond supportively and neutrally; ask clarifying questions when appropriate.",
  "response": "I hear you. It sounds like you are carrying a lot right now."
}
```

---

## Data Model

The backend persists data in a `conversations` table.

### Conversations Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| user_id | TEXT | User identifier |
| role | TEXT | `user` or `assistant` |
| message | TEXT | Message content |
| emotion | TEXT | Detected emotion label |
| confidence | REAL | Emotion confidence score |
| timestamp | DATETIME | Record creation timestamp |

---

## Configuration

### Environment Variables

Backend (`backend/.env`):

```env
GROQ_API_KEY=your_groq_api_key_here
```

Optional variables described in `.env.example`:

```env
DATABASE_URL=sqlite:///emotion_chatbot.db
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=False
FRONTEND_API_URL=http://localhost:8000
EMOTION_CONFIDENCE_THRESHOLD=0.6
GROQ_MODEL=mixtral-8x7b-32768
RESPONSE_TEMPERATURE=0.7
RESPONSE_TIMEOUT=15000
```

---

## Usage

1. Start backend and frontend servers.
2. Open the frontend in browser.
3. Send user messages through the chat input.
4. View detected emotion, selected strategy, and generated response from backend payload.
5. Continue conversation to build memory and trend context.

---

## Advantages

1. Emotion-aware conversational intelligence
2. Strategy-driven response control beyond plain prompting
3. Modular architecture for maintainability and extension
4. Persistent conversation memory for context continuity
5. Lightweight deployment with FastAPI, React, and SQLite

---

## Challenges Addressed

| Challenge | Solution |
|-----------|----------|
| Generic chatbot responses | Emotion detection plus strategy layer |
| LLM failures and instability | Defensive fallbacks and safe defaults |
| Context loss between messages | Conversation persistence in SQLite |
| Emotional drift over time | Trend analysis agent |
| Frontend-backend communication reliability | Axios timeout and structured error handling |

---

## Future Enhancements

### Phase 2
- Add authentication and user session management
- Add user-specific dashboards and conversation analytics

### Phase 3
- Add multi-language emotion detection
- Add advanced summarization and reflective insights

### Phase 4
- Add Docker and cloud deployment pipeline
- Add CI workflow with automated quality checks

### Phase 5
- Add role-based admin controls
- Add observability and centralized logging

---

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit with clear messages.
4. Run tests before opening pull request.
5. Submit a pull request with summary and test evidence.

---

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.

---

## Support

For support or collaboration requests, open a GitHub issue in the project repository.

