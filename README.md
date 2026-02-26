# Cloud Service Selection System for Startups

A decision-support web application that recommends a cloud provider (**AWS**, **Azure**, or **GCP**) and a service model (**IaaS**, **PaaS**, **SaaS**) based on your priorities and context. Built for startups and teams evaluating cloud options.

---

## Features

- **Weighted recommendation engine** — Prioritize budget, scalability, security, ease of use, and free tier via sliders; the system normalizes weights and returns the best-fit provider.
- **Service model suggestion** — Suggests IaaS, PaaS, or SaaS from industry and team expertise.
- **Live preview** — Real-time recommendation preview as you change sliders and dropdowns (debounced API calls).
- **Full result view** — Provider name, service model, score comparison bars, confidence indicator, explanation, and “Why not others?” summary.
- **PDF report** — Download a summary of your recommendation (uses jsPDF in the browser).
- **Health check** — API health endpoint for monitoring and load balancers.
- **Docker support** — Single container with gunicorn; optional `docker-compose` for one-command run.

---

## Tech Stack

| Layer | Stack |
|-------|--------|
| Backend | Python 3.11, Flask, gunicorn |
| Frontend | Vanilla JS, HTML5, CSS3 (no frameworks) |
| API | REST (JSON); POST `/recommend`, GET `/health` |
| Deployment | Docker, docker-compose; AWS Elastic Beanstalk–ready (Procfile) |

---

## Prerequisites

- **Python 3.11+** (for local run)
- **Docker** (optional; for containerized run)

---

## Quick Start

### Option 1: Run locally

```bash
# Clone the repo
git clone https://github.com/Parth4950/Cloud-Service-Selection-System-for-Startups.git
cd Cloud-Service-Selection-System-for-Startups

# Create virtual environment and install dependencies
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt

# Run the app (serves frontend + API on port 5001)
python run.py
```

Open **http://localhost:5001** in your browser.

### Option 2: Run with Docker

```bash
# Build and run
docker build -t cloud-selection .
docker run -p 5001:5001 cloud-selection
```

Or with Docker Compose:

```bash
docker-compose up --build
```

Then open **http://localhost:5001**.

---

## API

### Health check

```http
GET /health
```

**Response:** `200 OK`  
```json
{ "status": "ok", "service": "cloud-selection-backend" }
```

### Get recommendation

```http
POST /recommend
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `budget` | string | Yes | `"low"`, `"medium"`, `"high"` |
| `scalability` | string | Yes | `"low"`, `"medium"`, `"high"` |
| `security` | string | Yes | `"low"`, `"medium"`, `"high"` |
| `ease_of_use` | string | Yes | `"low"`, `"medium"`, `"high"` |
| `free_tier` | string | Yes | `"low"`, `"medium"`, `"high"` |
| `team_expertise` | string | Yes | `"low"`, `"medium"`, `"high"` |
| `industry` | string | Yes | `"general"`, `"fintech"`, `"healthcare"`, `"ai"` |
| `weights` | object | No | Optional custom weights: `budget`, `scalability`, `security`, `ease_of_use`, `free_tier` (numeric; normalized by backend) |

**Example:**

```json
{
  "budget": "high",
  "scalability": "medium",
  "security": "high",
  "ease_of_use": "low",
  "free_tier": "high",
  "team_expertise": "medium",
  "industry": "fintech"
}
```

**Response:** `200 OK`  
```json
{
  "recommended_provider": "aws",
  "recommended_service_model": "PaaS",
  "final_scores": { "aws": 7.2, "azure": 6.1, "gcp": 6.8 },
  "explanation": ["..."]
}
```

---

## Project Structure

```
├── app/
│   ├── __init__.py          # Flask app factory, routes for / and static
│   ├── routes.py            # /health, /recommend
│   └── core/
│       ├── config.py        # Provider catalog, weights, service model rules
│       ├── scoring_engine.py # Weighted scoring + optional custom weights
│       ├── service_model_rules.py # IaaS/PaaS/SaaS rules
│       └── explanation_engine.py  # Human-readable explanation
├── frontend/
│   ├── index.html           # SPA: landing, about, form, result
│   ├── style.css
│   ├── script.js            # Form, payload, preview debounce, submit
│   ├── api.js               # getRecommendation, getRecommendationWithSignal
│   ├── ui.js                # Screens, result render, PDF, preview
│   └── lib/
│       └── jspdf.umd.min.js # Optional; for PDF download (see lib/README.txt)
├── tests/
│   ├── test_scoring_engine.py
│   └── test_service_model_rules.py
├── run.py                   # WSGI entry (gunicorn run:app)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Procfile                 # Elastic Beanstalk
├── pytest.ini
└── README.md
```

---

## Testing

```bash
# With venv activated
pytest
```

Runs unit tests for the scoring engine and service model rules.

---

## License

MIT (or specify your license here).
