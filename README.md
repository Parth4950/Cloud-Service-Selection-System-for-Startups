# Cloud Service Selection System for Startups

A decision-support web application that recommends a cloud provider (AWS, Azure, or GCP) and a service model (IaaS, PaaS, or SaaS) based on configurable priorities such as budget, scalability, security, ease of use, and free tier. The system uses a weighted scoring engine and rule-based service model selection to produce a recommendation with an explanation and optional PDF report.

**Stack:** Flask (Python 3.11) backend; vanilla HTML, CSS, and JavaScript frontend. No database or front-end frameworks. Supports Docker and is suitable for deployment behind a production WSGI server (e.g. gunicorn) or platforms such as AWS Elastic Beanstalk.

---

## Features

- Configurable priority weights (sliders) with automatic normalization
- Live recommendation preview as inputs change (debounced API calls)
- Full result view: recommended provider, service model, score comparison, confidence indicator, and “why not others” summary
- Optional PDF download of the recommendation (client-side, via jsPDF)
- REST API: `GET /health` and `POST /recommend` with JSON request/response
- Docker and docker-compose support; Procfile included for Elastic Beanstalk

---

## Requirements

- **Python 3.11+** for local execution
- **Docker** (optional) for containerized execution

---

## Running the Application

### Local (Python)

```bash
git clone https://github.com/Parth4950/Cloud-Service-Selection-System-for-Startups.git
cd Cloud-Service-Selection-System-for-Startups

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python run.py
```

Then open **http://localhost:5001**. The server serves both the web UI and the API.

### Docker

```bash
docker build -t cloud-selection .
docker run -p 5001:5001 cloud-selection
```

Alternatively: `docker-compose up --build`. The application is available at **http://localhost:5001**.

---

## API Reference

**GET /health**  
Returns a minimal health payload for monitoring or load balancers.

- **Response (200):** `{"status": "ok", "service": "cloud-selection-backend"}`

**POST /recommend**  
Accepts a JSON body and returns a recommended provider, service model, scores, and explanation.

- **Required fields:** `budget`, `scalability`, `security`, `ease_of_use`, `free_tier`, `team_expertise`, `industry`
- **Allowed values:** For the first six fields: `"low"`, `"medium"`, `"high"`. For `industry`: `"general"`, `"fintech"`, `"healthcare"`, `"ai"`.
- **Optional:** `weights` — object with keys `budget`, `scalability`, `security`, `ease_of_use`, `free_tier` (numeric values; the backend normalizes them).

Example request body:

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

Response includes `recommended_provider`, `recommended_service_model`, `final_scores` (per provider), and `explanation` (list of strings).

---

## Project Structure

| Path | Description |
|------|-------------|
| `app/` | Flask application: routes (`/health`, `/recommend`), core logic (config, scoring, service-model rules, explanation generation) |
| `frontend/` | Single-page UI: HTML, CSS, JS (script, api, ui). PDF dependency: `frontend/lib/jspdf.umd.min.js` (see `frontend/lib/README.txt` if missing) |
| `tests/` | Pytest tests for scoring and service model rules |
| `run.py` | Application entry point; use `gunicorn -w 2 -b 0.0.0.0:5001 run:app` for production |
| `Dockerfile`, `docker-compose.yml` | Container build and run configuration |
| `Procfile` | Elastic Beanstalk process definition |

---

## Testing

With the virtual environment activated:

```bash
pytest
```

Runs unit tests for the scoring engine and service model rules.
