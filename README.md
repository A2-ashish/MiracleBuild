# Miracle Build

> A multi-stage generation pipeline that compiles natural language descriptions into structured, validated, executable application configurations.

![Architecture](docs/architecture.png)

## 🌟 What is Miracle Build?

Miracle Build is **not** a chatbot or prompt engineering wrapper. It's an **engineered compiler system** that treats natural language as source code and produces a complete, validated, executable application configuration through a rigorous multi-stage pipeline.

```
Natural Language → Intent Extraction → System Design → Schema Generation → Refinement → Validation & Repair → Executable Config → Runtime
```

## 🏗️ Architecture

### Compiler Pipeline (5 Stages)

| Stage | Compiler Analog | Purpose |
|-------|----------------|---------|
| **1. Intent Extraction** | Lexer/Tokenizer | Parse entities, features, roles, constraints from natural language |
| **2. System Design** | Parser/AST | Define entity relationships, user flows, permission matrix |
| **3. Schema Generation** | Code Generation | Generate DB, API, UI, Auth, Business Logic schemas |
| **4. Refinement** | Optimizer | Cross-layer consistency resolution and deduplication |
| **5. Validation & Repair** | Linker/Verifier | 12 cross-layer checks + targeted auto-repair |

### Output Schemas

The compiler produces a unified `AppConfig` containing:
- **Database Schema** — Tables, columns, types, constraints, relations, indexes
- **API Schema** — RESTful endpoints, methods, request/response schemas, auth requirements
- **UI Schema** — Pages, components, layouts, navigation, theming, data bindings
- **Auth Schema** — Roles, permissions, password policy, session config
- **Business Logic** — Rules, conditions, actions, workflows, premium gating

### Validation Engine (12 Cross-Layer Checks)

1. API fields match DB columns
2. UI data sources bind to valid API endpoints
3. Auth roles consistent across all layers
4. Foreign key references valid
5. CRUD completeness for every entity
6. Navigation maps to existing pages
7. Business rules reference valid entities
8. Permission matrix complete
9. Unique API paths and page routes
10. Form fields match API POST body
11. Table columns match API GET response
12. Premium gating consistent in UI and API

### Repair Engine

When validation fails, the system uses **targeted repair** — not brute-force retry:
- **Structural repairs** (deterministic): Add missing fields, fix types
- **Cross-layer repairs**: Propagate changes across layers
- **Semantic repairs** (LLM-assisted): Regenerate only the broken part

### Runtime Renderer

The generated config is directly executable via a browser-based runtime that:
- Renders pages with appropriate layouts
- Generates forms from API schemas
- Populates tables with realistic mock data
- Applies theming and navigation
- Enforces role-based visibility

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run Evaluation
```bash
cd backend
python -m app.evaluation.runner
```

## 📊 Evaluation Framework

### Test Suite
- **10 real product prompts**: CRM, e-commerce, LMS, healthcare, HR, etc.
- **10 edge cases**: Vague prompts, conflicting requirements, nonsensical input, domain jargon

### Tracked Metrics
| Metric | Description |
|--------|-------------|
| Success Rate | % of prompts producing valid executable config |
| Retry Count | Number of repair cycles needed |
| Latency | End-to-end and per-stage timing |
| Token Usage | Total tokens consumed |
| Cost | USD cost estimate |
| Cross-Layer Score | % of validation checks passing |

## 💰 Cost vs Quality Tradeoff

| Model | Avg Latency | Avg Cost | Quality Score |
|-------|-------------|----------|---------------|
| gemini-2.5-pro | ~30s | ~$0.05 | High |
| gemini-2.5-flash | ~10s | ~$0.008 | Medium-High |
| gemini-2.0-flash | ~5s | ~$0.003 | Medium |

## 🛠️ Tech Stack

- **Backend**: Python 3.11 / FastAPI / Pydantic v2
- **Frontend**: Vite / React
- **LLM**: Google Gemini API (configurable model)
- **Validation**: 12-point cross-layer consistency engine
- **Runtime**: Browser-based React renderer

## 📁 Project Structure

```
appforge-compiler/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── pipeline/            # 5-stage compiler pipeline
│   │   ├── schemas/             # Pydantic models (strict contracts)
│   │   ├── validation/          # Validation & repair engine
│   │   ├── llm/                 # LLM client & prompts
│   │   ├── evaluation/          # Test suite & metrics
│   │   └── failure/             # Failure handling
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── runtime/             # App config renderer
│   │   └── hooks/               # React hooks
│   └── package.json
└── README.md
```

## 📄 License

MIT
