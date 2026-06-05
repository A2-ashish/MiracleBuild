# ⚡ Miracle Build - Comprehensive Project Documentation

**Live URL:** [https://miracle-build.vercel.app/](https://miracle-build.vercel.app/)  
**Repository:** [https://github.com/A2-ashish/MiracleBuild](https://github.com/A2-ashish/MiracleBuild)

Miracle Build is an advanced, AI-powered application compiler that takes natural language prompts (or voice inputs) and deterministically generates full-stack application blueprints. It features a robust 5-stage compilation pipeline, automatic self-repair mechanics, and API key rotation for seamless scale.

---

## 1. System Architecture

Miracle Build operates on a decoupled Client-Server architecture utilizing Server-Sent Events (SSE) for real-time streaming of compilation stages.

### The 5-Stage LLM Pipeline
The core of Miracle Build is a deterministic pipeline that breaks complex application generation into isolated, manageable reasoning steps:

1. **Stage 1 — Intent Extraction:** Parses the user's natural language prompt into structured JSON identifying core entities, necessary features, and user roles.
2. **Stage 2 — System Architecture:** Designs the high-level architecture, establishing Entity-Relationship mappings (e.g., One-to-Many) and User Flows.
3. **Stage 3 — Schema Generation:** Parallel LLM calls generate granular code schemas:
   - Database Schemas (Tables, Columns, Indexes, Foreign Keys)
   - API Schemas (REST endpoints, Request/Response bodies)
   - UI Schemas (Components, Forms, Dashboards, Navigation)
   - Auth & Business Logic (Role-Based Access Control, computed fields)
4. **Stage 4 — Refinement:** Cross-checks all generated schemas across layers to ensure cohesion (e.g., ensuring a UI form field perfectly matches a Database column).
5. **Stage 5 — Validation & Repair:** Runs 12 rigorous structural and semantic checks. If the generated output fails a check, it enters an LLM-assisted **Repair Loop** (up to 3 cycles) to automatically fix the inconsistencies before returning the final JSON blueprint.

---

## 2. Technology Stack

### Frontend (Client)
- **Framework:** React + Vite
- **Styling:** Vanilla CSS tailored to an **Apple Minimalist Light Mode** aesthetic (soft gray backgrounds, stark white cards, diffuse shadows, translucent frosted-glass headers).
- **Interactivity:** 
  - **Web Speech API** for native Voice-to-Text command dictation.
  - Real-time Pipeline Visualizer updating via SSE.
  - Interactive JSON schema tabs for deeply exploring generated application structures.
- **Deployment:** Vercel

### Backend (Compiler API)
- **Framework:** FastAPI (Python 3.12)
- **Validation:** Pydantic `BaseModel` for strict structural LLM output parsing.
- **AI Integration:** `google-genai` using Gemini 2.5 Flash and Gemini 2.5 Pro.
- **Dependency Management:** `uv` — an extremely fast Rust-based Python package installer.
- **Deployment:** Render (Automated via `render.yaml` Blueprint or managed Web Service)

---

## 3. Key Methodologies & Engineering Marvels

### Dynamic API Key Rotation
To bypass global rate limits (`HTTP 429 Quota Exhaustion`) on free-tier LLM API keys, Miracle Build implements a resilient, multi-key rotation engine. The `LLMClient` dynamically captures 429 errors and silently rotates through an array of 22 backup keys, ensuring high availability and seamless prompt execution regardless of load.

### Deterministic JSON Extraction
LLMs can be unpredictable. Miracle Build enforces stability by:
- Injecting strict JSON-schema examples into the system prompts.
- Utilizing a specialized JSON extraction regex to strip markdown blocks (```json ... ```) from raw LLM responses.
- Parsing the strings through granular Pydantic models.

### Evaluation Framework
The project includes a standalone `runner.py` evaluation suite. It tests the compiler against 20 incredibly complex prompts (e.g., "Build an enterprise CRM with PDF generation") to measure:
- Pipeline completion duration
- Token usage and estimated cost metrics
- Self-repair cycle frequency
- Validation success rate

### Server-Sent Events (SSE) Streaming
Instead of forcing the user to wait 30-40 seconds for a massive JSON payload, the backend yields updates asynchronously via `sse-starlette`. As each pipeline stage completes, a JSON payload is streamed to the React frontend, which instantly updates the glowing UI pipeline visualizer.

---

## 4. User Interface & Aesthetics
The application utilizes a premium design system:
- **Voice Commands:** A microphone button `🎤` actively listens, transcribes, and appends user ideas directly into the input.
- **Apple-Style Minimalism:** Uncluttered negative space, high legibility `Inter` typography, and fully rounded elements mimic the native macOS experience.
- **Subtle Glassmorphism:** A saturated blur effect on the sticky top navigation header refracts the content scrolling underneath it.

---

## 5. Deployment Guide

### Vercel (Frontend)
1. Hosted automatically via GitHub integration.
2. Build Command: `npm run build` (tsc && vite build)
3. Env Var: `VITE_API_URL` pointing to the Render backend.

### Render (Backend)
The backend is highly optimized for Python 3.12 utilizing `uv`.
- **Build Command:** `pip install uv && uv venv && uv pip install --python .venv -r requirements.txt`
- **Start Command:** `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port:** Dynamically assigned by Render (`$PORT`).
