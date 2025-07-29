# 🧪 HC API Platform

A lightweight, developer-friendly API mocking platform inspired by Beeceptor/Postman mock servers. Create, organize, and test mock HTTP endpoints with ease.

---

## 🚀 Features

- 🧱 Dynamic API mock rules with path/method matching
- 🔐 JWT authentication support
- 📄 Templated responses using PyBars
- 🗃 PostgreSQL database via SQLAlchemy ORM
- ⚙️ Environment-based config with `python-dotenv`
- 🐳 Docker + Compose ready
- 🎨 Minimal web UI for managing mocks and projects

---

## 📁 Project Structure

```
HC_API_Plat/
├── app/
│   ├── crud.py              # DB operations
│   ├── db.py                # SQLAlchemy session setup
│   ├── models.py            # ORM models
│   ├── routes_api.py        # REST API routes
│   ├── routes_mock.py       # Mock logic routes
│   ├── routes_ui.py         # Frontend HTML pages
│   ├── template_engine.py   # Template rendering (PyBars)
│   ├── static/              # CSS/JS assets
│   └── templates/           # HTML templates
├── run.py                   # Flask entry point
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Multi-container setup
├── Dockerfile               # App Docker build
├── pytest.ini               # Pytest config
├── .env                     # Env variables
└── tests/                   # Test suite
```

---

## ⚙️ Setup

### 1. Clone & Configure

```bash
git clone https://your-repo-url.git
cd HC_API_Plat
cp .env.example .env  # If applicable
```

Edit `.env` and update the values for:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- etc.

### 2. Run via Docker

```bash
docker-compose up --build
```

App will be available at:
- UI: `http://localhost:5001/`
- API: `http://localhost:5001/api`
- Mock: `http://localhost:5001/test/<project>/<endpoint>`

---

## 🔐 Authentication

- Login via `/api/login` with valid credentials
- Use JWT in headers:

```
Authorization: Bearer <your-token>
```

---

## 🧪 Example Workflow

### Create Project

```http
POST /api/projects
{
  "name": "MyService"
}
```

### Add Mock Rule

```http
POST /api/rules
{
  "project": "myservice",
  "method": "GET",
  "endpoint": "/status",
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "body": { "status": "ok" }
  }
}
```

Then test via:

```
GET http://localhost:5001/test/myservice/status
```

---

## 📦 Dependencies

From `requirements.txt`:

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.2
Flask-JWT-Extended==4.7.1
python-dotenv==1.0.0
psycopg2-binary==2.9.6
Werkzeug>=2.3.7
pybars3
pytest
```

---

## 📝 License

MIT License.

---

## 👨‍💻 Author

**Duong Tuan**  
GitLab: [@qtuan971](https://gitlab.com/qtuan971)
