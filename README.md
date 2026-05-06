🧠 Jarvis AI System

An advanced modular AI assistant designed to behave like a real-time human operator sitting beside you — capable of understanding tasks, planning actions, executing commands, and interacting across multiple platforms.

---

🚀 What is this?

Jarvis AI System is a multi-layer AI assistant built with a scalable architecture.

It is designed to:

- Understand user input (text/voice)
- Plan tasks like a human
- Execute commands using tools
- Store memory (short + long term)
- Work across devices (Android, Windows)

👉 Think of it as your personal AI operator

---

🏗️ Architecture Overview

User → API → Brain → Planner → Tools → Execution
                     ↓
                  Memory

---

📂 Project Structure

server/
 ├── app/
 │   ├── api/            # Routes & schemas
 │   ├── core/           # Brain, config, logging
 │   ├── db/             # Database models
 │   ├── planner/        # Task planning logic
 │   ├── services/       # LLM, memory, tools
 │   ├── tools/          # Execution tools
 │   ├── memory/         # Memory system
 │   ├── queue/          # Async tasks (future)
 │   └── main.py         # Entry point

android_app/             # Mobile app (Flutter)
windows_agent/           # System automation

docs/                    # Docs & roadmap
tests/                   # Testing
scripts/                 # Setup scripts

---

⚙️ Tech Stack

- Backend: FastAPI
- AI Model: Gemini
- Mobile: Flutter
- Language: Python

---

🧩 Features

✅ Current (Phase 1–4)

- API-based AI assistant
- Modular architecture
- Gemini integration
- Basic task planning
- Tool execution system

---

🔄 Upcoming (Phase 5–6)

- Autonomous task execution
- Voice interaction
- OS control (Windows agent)
- Advanced memory system
- Multi-device sync

---

🛠️ Setup & Run

1. Clone Repo

git clone https://github.com/omharde42/jarvis-ai-system.git
cd jarvis-ai-system/server

---

2. Create Virtual Environment

python -m venv venv
venv\Scripts\activate

---

3. Install Dependencies

pip install -r requirements.txt

---

4. Create ".env" file

GEMINI_API_KEY=your_api_key_here

---

5. Run Server

python -m uvicorn app.main:app --reload

---

6. Open API

http://127.0.0.1:8000/docs

---

📡 API Endpoints

- "/jarvis" → Main AI interaction
- "/phases/status" → Check system phase

---

🧠 How It Works

1. User sends request
2. API receives input
3. Brain processes intent
4. Planner creates steps
5. Tools execute tasks
6. Memory stores data
7. Response is returned

---

🎯 Vision

Build a real AI assistant that:

- Thinks before acting
- Executes real-world tasks
- Learns continuously
- Feels like a human assistant

---

📌 Roadmap

- Phase 1 → Core API ✔
- Phase 2 → Tools ✔
- Phase 3 → Memory ✔
- Phase 4 → Integration ✔
- Phase 5 → Automation 🚧
- Phase 6 → Full AI 🚧

---

👨‍💻 Author

Om Harde
🚀 Building next-gen AI systems
