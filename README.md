```
Healthcare-agent/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner_agent.py
│   │   ├── question_service.py
│   │   ├── medical_data_service.py
│   │   ├── validation_engine.py
│   │   ├── decision_engine.py
│   │   ├── recommendation_engine.py
│   │   └── explanation_engine.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── knowledge/
│   │   ├── disease_guidelines.json
│   │   └── hospital_data.json
│   ├── chroma/
│   │   └── chroma_setup.py
│   ├── config.py
│   └── main.py
├── frontend/
│   └── app.py
├── tests/
│   └── test_planner.py
├── .env.example
├── requirements.txt
└── README.md
```

# Healthcare Planning Assistant Agent

A full-stack, multi-agent AI system for healthcare treatment planning powered by **Google Gemini**, **FastAPI**, **Streamlit**, **PostgreSQL**, and **ChromaDB**.

---

## Architecture Overview

```
[Streamlit UI]  ──►  [FastAPI]  ──►  [PlannerAgent]
                                        │
              ┌─────────────────────────┤
              │                         │
     [QuestionService]        [DecisionEngine (Gemini)]
     [ValidationEngine]       [RecommendationEngine]
     [MedicalDataService]     [ExplanationEngine]
              │
        [PostgreSQL]  [ChromaDB]  [JSON Knowledge Files]
```

---

## Tech Stack

| Layer           | Technology                    |
|-----------------|-------------------------------|
| Frontend        | Streamlit                     |
| Backend         | FastAPI + Uvicorn             |
| LLM             | Google Gemini API             |
| Agent Framework | Custom Planner (+ LangChain)  |
| DB (Structured) | PostgreSQL + SQLAlchemy       |
| DB (Vector)     | ChromaDB                      |
| Knowledge Store | JSON files                    |

---

## Setup Instructions

### 1. Clone and enter the project
```bash
git clone <repo-url>
cd Healthcare-agent
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
copy .env.example .env       # Windows
# OR
cp .env.example .env         # Linux/Mac
```
Edit `.env` and fill in:
- `GEMINI_API_KEY` — your Google AI Studio API key
- `DATABASE_URL` — your PostgreSQL connection string

### 5. Create the PostgreSQL database
```sql
CREATE DATABASE healthcare_agent;
```

### 6. Initialize the database tables
```bash
cd backend
python -c "import asyncio; from db.database import init_db; asyncio.run(init_db())"
```

### 7. Seed ChromaDB with knowledge
```bash
cd backend
python chroma/chroma_setup.py
```

### 8. Start the FastAPI backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 9. Start the Streamlit frontend (new terminal)
```bash
cd frontend
streamlit run app.py
```

---

## API Endpoints

| Method | Endpoint                | Description                        |
|--------|-------------------------|------------------------------------|
| POST   | `/api/session/start`    | Start a new user session           |
| POST   | `/api/plan/start`       | Submit goal and launch PlannerAgent|
| POST   | `/api/plan/respond`     | Submit answers to medical questions|
| GET    | `/api/plan/{session_id}`| Retrieve the final treatment plan  |
| GET    | `/health`               | Health check                       |

---

## Output Format

```json
{
  "treatment_plan": {
    "disease_type": "Breast Cancer",
    "treatment_type": "Chemotherapy + Surgery",
    "timeline": "6 months",
    "notes": "Stage II, surgery allowed"
  },
  "recommended_hospitals": [
    {
      "name": "Apollo Cancer Centre",
      "location": "Mumbai",
      "type": "Oncology",
      "priority_rank": "1"
    }
  ],
  "explanation": "Based on your Stage II breast cancer profile...",
  "disclaimer": "This is not a medical diagnosis. Consult a licensed medical professional."
}
```

---

## Running Tests
```bash
pytest tests/ -v
```

---

## Agent Execution Flow

```
User Goal → PlannerAgent
  → decomposeGoal()
  → QuestionService (ask questions)
  → MedicalDataService (store profile)
  → ValidationEngine (validate)
    └─ if incomplete → back to QuestionService
  → DecisionEngine (Gemini reasoning)
  → RecommendationEngine (rank hospitals)
  → ExplanationEngine (format output)
  → Return structured JSON
```
