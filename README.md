# HC API Platform

A **Beeceptor-like API mocking and testing platform** built with **Flask** and **PostgreSQL**.  
This platform lets you create projects, define mock rules (static or dynamic), and intercept API requests with custom responses.  
Includes a simple web UI and JWT-based authentication.

---

## 🚀 Features

- **User Authentication (JWT)**: Secure registration and login.
- **Project Management**: Organize rules under multiple projects.
- **Dynamic Mock Rules**:
  - Supports **path regex** (`^/api/users/(?P<username>[a-zA-Z0-9_]+)$`).
  - Access request data with placeholders:
    - `{{body.username}}` → Request body
    - `{{query.page}}` → Query parameters
    - `{{headers.Authorization}}` → Headers
    - `{{username}}` → Path regex captured groups
    - `{{db.password_hash}}` → Database lookups (auto-fetched by username)
- **Request Logging**: Automatically logs requests and responses.
- **Web UI**: Manage projects, rules, and view logs.
- **Docker Support**: Ready-to-use `docker-compose.yml`.
- **Testing Ready**: Includes pytest.

---

## 🛠️ Tech Stack

- **Backend**: Flask, Flask-JWT-Extended, SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Templating**: Handlebars-like engine for dynamic placeholders
- **Containerization**: Docker & Docker Compose

---

## 📦 Installation

### 1. Clone & Enter Project

```bash
git clone <your_repo_url>
cd HC_API_Plat
```

### 2. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables

Edit **`.env`**:

```
FLASK_ENV=development
DATABASE_URL=postgresql://fakeuser:fakepass@db:5432/fakeapi
JWT_SECRET_KEY=your_secret_key
```

---

## ▶️ Running the Project

### **Option 1: Run Locally**

```bash
export FLASK_APP=run.py
flask run
```

Server runs at: [http://localhost:5000](http://localhost:5000)

### **Option 2: Run with Docker**

```bash
docker-compose up --build
```

- Flask API → `http://localhost:5000`  
- PostgreSQL → `localhost:5432` (`fakeuser` / `fakepass` / `fakeapi`)

---

## 🔑 Authentication

### Register

`POST /api/auth/register`

```json
{
  "username": "duongtuan",
  "password": "123123"
}
```

### Login

`POST /api/auth/login`

```json
{
  "username": "duongtuan",
  "password": "123123"
}
```

Returns:

```json
{
  "access_token": "<JWT_TOKEN>"
}
```

Include JWT in all further API calls:

```
Authorization: Bearer <JWT_TOKEN>
```

---

## 📂 Project Management

### Create Project

`POST /api/projects`

```json
{
  "name": "My Test Project",
  "base_url": "/api",
  "description": "Testing API mock rules"
}
```

### List Projects

`GET /api/projects`

---

## 🎭 Creating Mock Rules

Rules belong to projects (`project_id` required).

### Example Rule (Login)

`POST /api/projects/<project_id>/rules`

```json
{
  "method": "POST",
  "path_regex": "^/api/login$",
  "status_code": 200,
  "headers": {"Content-Type": "application/json"},
  "body_template": {
    "template": "{\"message\": \"Welcome {{body.username}}\", \"page\": \"{{query.page}}\"}"
  },
  "enabled": true,
  "delay": 0
}
```

### Example Rule (Path + DB)

```json
{
  "method": "GET",
  "path_regex": "^/api/users/(?P<username>[a-zA-Z0-9_]+)$",
  "status_code": 200,
  "headers": {"Content-Type": "application/json"},
  "body_template": {
    "template": "{\"username\": \"{{username}}\", \"password\": \"{{db.password_hash}}\"}"
  },
  "enabled": true
}
```

---

## 🔄 Dynamic Placeholders

| Placeholder Type | Example | Value Source |
|-------------------|---------|--------------|
| **Body** | `{{body.username}}` | JSON body field |
| **Query** | `{{query.page}}` | URL query params |
| **Headers** | `{{headers.Authorization}}` | Request headers |
| **Path** | `{{username}}` | Named regex groups |
| **Database** | `{{db.password_hash}}` | DB lookup (auto by username) |

---

## 🪵 Viewing Logs

### List Logs

`GET /api/logs`

Returns:

```json
[
  {
    "method": "POST",
    "path": "/api/login",
    "status_code": 200,
    "matched_rule_id": 1,
    "body": "{\"username\": \"duongtuan\"}",
    "query": {},
    "timestamp": "2025-07-25T10:30:00"
  }
]
```

---

## 🧪 Testing

Run all tests:

```bash
pytest -v
```

---

## 📸 Web UI

- **/register** – Register new users  
- **/projects** – Manage projects and rules  
- **/logs** – View logs  

---

## 📜 License

MIT License

---

**Author:** Duong Tuan
