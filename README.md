# 🧪 HC API Platform

A lightweight, developer‑friendly API mocking platform inspired by Beeceptor/Postman mock servers. Define and organize dynamic mock HTTP endpoints with ease, all backed by PostgreSQL and delivered via a minimal Flask UI and JSON API.

---

## 🚀 Features

- 🧱 **Dynamic Mock Rules**: Match requests by HTTP method, path, query parameters, headers, or JSON body.
- 🔄 **Name Normalization**: User‑entered project names are normalized (lowercase, spaces → underscores, strip extra punctuation) automatically—so URLs are always safe.
- 🔐 **JWT Authentication**: Secure API and UI endpoints with JSON Web Tokens via Flask-JWT-Extended.
- 📄 **Templated Responses**: Handlebars‑style templates powered by PyBars allow injecting request data into response bodies and headers.
- 🗃 **PostgreSQL Persistence**: Store projects, rules, and request logs in JSONB fields using SQLAlchemy ORM.
- ⚙️ **Environment‑Based Config**: Manage secrets and database URLs with python-dotenv (`.env`).
- 🐳 **Containerized**: Ready to run with Docker and Docker Compose for development or production.
- 🎨 **Minimal Web UI**: Manage users, projects, rules, and view live request logs via Jinja2 + Bootstrap with vanilla JS.
- 🧪 **Test Suite**: Pytest framework configured for easy expansion of unit and integration tests.

---

## 📁 Project Structure

```
HC_API_Plat/
├── .env                   # Environment variables (DATABASE_URL, JWT_SECRET_KEY, etc.)
├── Dockerfile             # Flask app container definition
├── docker-compose.yml     # Defines Flask + Postgres services
├── requirements.txt       # Python dependencies
├── pytest.ini             # Pytest configuration
├── run.py                 # Flask entry point (create_app + app.run)
├── app/
│   ├── __init__.py        # App factory, extension + blueprint registration
│   ├── db.py              # SQLAlchemy setup
│   ├── models.py          # ORM models (Project, MockRule, LoggedRequest)
│   ├── crud.py            # Database operations (create_project normalizes name)
│   ├── utils.py           # Name normalization helper (`normalize_project_name`)
│   ├── template_engine.py # PyBars rendering logic
│   ├── routes_api.py      # JSON API endpoints under `/api`
│   ├── routes_ui.py       # Jinja2 templates for UI
│   ├── routes_mock.py     # Catch‑all mock server (`/<normalized_name>/<path>`)
│   ├── static/            # CSS and JS assets
│   └── templates/         # HTML templates for UI pages
└── tests/                 # Pytest tests (unit & integration)
```

---

## ⚙️ Setup

1. **Clone the repo**:
   ```bash
   git clone https://gitlab.com/<YourGroup>/hc_api_plat.git
   cd hc_api_plat
   ```
2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env: set DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY, POSTGRES_* vars
   ```

---

## 🐳 Running with Docker

Bring up the app and database:

```bash
docker-compose up --build
```

- **UI & Mock Server**: http://localhost:5000/
- **API**:         http://localhost:5000/api

Queries to mocks use the normalized project name:
```
GET http://localhost:5000/<normalized_name>/<endpoint>
```  
(e.g. `/my_project/status`)

---

## 🏃‍♂️ Local Development

> Requires Python 3.11 and a local Postgres instance (or docker-compose).

1. Create and activate a virtualenv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize or migrate the database:
   ```bash
   flask db upgrade
   ```
4. Run the app:
   ```bash
   flask run
   ```
5. Open http://localhost:5000/ in your browser.

---

## 🔐 Authentication

- **Register**: `POST /api/users/register` with `{ "username": "alice", "password": "…" }`
- **Login**:    `POST /api/users/login` → receives `{ "access_token": "…" }`
- **Protected endpoints** require header:
  ```http
  Authorization: Bearer <access_token>
  ```

---

## 🧪 Example Workflow

### 1. Log In
- Open the application in your browser.
- Click **Login**, enter your username and password, then submit.
- After a successful login, you’ll be taken to your dashboard.

### 2. Create a Project
- Click **New Project**.
- Enter **My Service 1.0** as the project name and click **Create**.
- The platform will automatically normalize this to **my_service_1.0** for use in URLs.

### 3. Define Mock Rules
- Select your project and go to the **Rules** section.
- Click **Add Rule** and fill in the form:
  - **Method**: GET
  - **Endpoint**: `/status`
  - **Response Status**: 200
  - **Response Headers**: `Content-Type: application/json`
  - **Response Body**:
    ```json
    { "status": "ok", "type": "{{query.type}}" }
    ```
- Click **Save** to store the rule.

### 4. Test the Mock
- Open Postman (or any HTTP client).
- Create a **GET** request to:
  ```
  http://localhost:5000/test/my_service_1.0/status?type=success
  ```
- Send the request.
- You should see a JSON response like:
  ```json
  { "status": "ok", "type": "success" }
  ```

### 5. Check Logs
- In the UI, navigate to **Logs** under your project to view recent requests.
- Alternatively, via API send a **GET** request to `/api/logs?project_id=1&limit=50` and examine the returned list.

---

## 🛠 API Reference

| Method | Endpoint               | Description                     |
|--------|------------------------|---------------------------------|
| POST   | `/api/users/register`  | Create a new user               |
| POST   | `/api/users/login`     | User login, returns JWT token   |
| GET    | `/api/projects`        | List all projects               |
| POST   | `/api/projects`        | Create a project (normalizes name) |
| GET    | `/api/rules`           | List rules (filter by project)  |
| POST   | `/api/rules`           | Create a new mock rule          |
| PUT    | `/api/rules/{id}`      | Update existing rule            |
| DELETE | `/api/rules/{id}`      | Delete a rule                   |
| GET    | `/api/logs`            | List request logs               |
| DELETE | `/api/logs`            | Clear logs for a project        |

---

## ✅ Testing

Run the full test suite with pytest:
```bash
pytest --maxfail=1 --disable-warnings -q
```

---

## 🚀 Deployment

- **Docker Compose**: as above.
- **Heroku**: add a `Procfile`:
  ```Procfile
  web: gunicorn run:app
  ```
- **CI/CD**: integrate with GitLab CI, GitHub Actions, or other pipelines to build and push Docker images.

---

## 🤝 Contributing

1. Fork the repository and create a branch: `git checkout -b feature/XYZ`
2. Commit your changes with descriptive messages.
3. Push and open a merge request.
4. Ensure all tests pass before requesting review.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Author:** Duong Tuan ([qtuan971](https://gitlab.com/qtuan971))
