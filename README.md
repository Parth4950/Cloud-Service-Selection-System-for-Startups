# Cloud Service Selection System for Startups

Helps you pick a cloud provider (AWS, Azure, or GCP) and a service model (IaaS, PaaS, SaaS) based on what you care about—budget, scalability, security, etc. You set your priorities with sliders and dropdowns, and it gives you a recommendation plus a short explanation.

**What you get:** A small web app with a form, live preview as you tweak settings, full result with score bars and “why not the others,” and an optional PDF download. Backend is Flask; frontend is plain HTML/CSS/JS. No database, no frameworks on the front.

---

## How to run it

You need **Python 3.11+**. Docker is optional.

**Local (no Docker):**

```bash
git clone https://github.com/Parth4950/Cloud-Service-Selection-System-for-Startups.git
cd Cloud-Service-Selection-System-for-Startups

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python run.py
```

Then open **http://localhost:5001**. The app serves both the UI and the API from there.

**Docker:**

```bash
docker build -t cloud-selection .
docker run -p 5001:5001 cloud-selection
```

Or `docker-compose up --build`. Same URL.

---

## API in short

- **GET /health** — Returns `{"status":"ok", "service":"cloud-selection-backend"}`. Good for checks.
- **POST /recommend** — Send JSON with: `budget`, `scalability`, `security`, `ease_of_use`, `free_tier`, `team_expertise`, `industry` (all required). Values like `"low"`, `"medium"`, `"high"` for the first six; `industry` is `"general"`, `"fintech"`, `"healthcare"`, or `"ai"`. You can also send a `weights` object to tune how much each factor matters (backend normalizes it).

Example body:

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

You get back the recommended provider, service model, final scores for all three providers, and an explanation list.

---

## What’s in the repo

- **app/** — Flask app: `routes.py` for `/health` and `/recommend`, `core/` for config, scoring, service-model rules, and explanation text.
- **frontend/** — Single-page app: `index.html`, `style.css`, `script.js`, `api.js`, `ui.js`. PDF download uses jsPDF from `frontend/lib/` (see that folder’s README if the file is missing).
- **tests/** — Pytest tests for scoring and service model logic. Run with `pytest`.
- **run.py** — Entry point. Use `gunicorn -w 2 -b 0.0.0.0:5001 run:app` for production. There’s a Dockerfile and docker-compose and a Procfile for Elastic Beanstalk if you need them.

That’s it. If something’s broken, check that you’re on Python 3.11+ and that the backend is running on 5001 when you open the page.
