# LivestockOS — Backend Service

Standalone, production-ready FastAPI backend for the **LivestockOS** livestock health intelligence and herd monitoring application.

---

## Architecture & Features

- **Framework**: FastAPI (Python 3.10+) with async request handling
- **Database & ORM**: PostgreSQL (production/docker) & SQLite (local dev), powered by **SQLAlchemy 2.0** and **Alembic** migrations
- **Validation**: Pydantic v2 schemas separate from ORM models
- **Security & Auth**: Email/password authentication, passwords hashed with bcrypt, signed JWT access and refresh tokens, token revocation on logout, role-based access control (`FARMER`, `ADMIN`, `WORKER`), and multi-tenant farm data isolation
- **Rule & Intelligence Engine**: Automatic veterinary threshold evaluation for body temperature (fever/hypothermia), rumination anomalies, lethargy/inactivity, dynamic composite health scoring (0–100), and automated alert creation
- **API Endpoints**: Full CRUD and analytics for Animals, Sensors, Readings, Alerts, Dashboard, and QR Identification Tag Lookup
- **API Documentation**: Interactive Swagger/OpenAPI documentation at `/docs` and ReDoc at `/redoc`

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app instance, CORS, standardized error handlers
│   ├── core/
│   │   ├── config.py        # Settings via pydantic-settings, loads .env
│   │   └── security.py      # Password hashing (bcrypt) and JWT encode/decode
│   ├── db/
│   │   ├── base.py          # SQLAlchemy 2.0 Declarative Base
│   │   └── session.py       # Async engine & session factory
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # Farmers & Users
│   │   ├── animal.py        # Cattle & Herd records
│   │   ├── sensor.py        # BLE hardware sensors
│   │   ├── reading.py       # Time-series telemetry
│   │   ├── alert.py         # Health notifications
│   │   ├── health_score.py  # Composite score breakdowns
│   │   └── token_blacklist.py# Revoked refresh tokens
│   ├── schemas/             # Pydantic v2 validation models
│   │   ├── auth.py, user.py, animal.py, sensor.py
│   │   ├── reading.py, alert.py, dashboard.py, analytics.py, qr.py
│   ├── services/            # Isolated business logic layer
│   │   ├── auth_service.py, animal_service.py, sensor_service.py
│   │   ├── telemetry_service.py, alert_service.py
│   │   └── dashboard_service.py, analytics_service.py
│   └── api/
│       ├── deps.py          # get_db, get_current_user, require_roles
│       └── routes/          # Domain routers (auth, animals, alerts, etc.)
├── alembic/                 # Async Alembic migrations
├── tests/                   # Pytest automated test suite (24 tests)
├── CONTRACT.md              # Detailed API contract specification
├── seed.py                  # Seed script populating demo herd and farmers
├── requirements.txt         # Pinned Python dependencies
├── Dockerfile               # Container build definition
├── docker-compose.yml       # Multi-container PostgreSQL + FastAPI stack
└── .env.example             # Documented environment configuration
```

---

## Quick Start with Docker Compose (Recommended)

Start both PostgreSQL 16 and the FastAPI application with a single command:

```bash
cd backend
docker-compose up --build
```

Docker Compose will automatically:
1. Start and health-check the PostgreSQL container on port `5432`.
2. Apply Alembic migrations (`alembic upgrade head`).
3. Seed sample farmers, cattle, sensors, and vitals (`python seed.py`).
4. Start Uvicorn/Gunicorn on port `8000`.

Open **http://localhost:8000/docs** in your browser to inspect and try the interactive API documentation.

---

## Local Development Setup

### 1. Prerequisites
- Python 3.10+ installed
- PostgreSQL (or use built-in SQLite for zero-setup local dev)

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

To run with local SQLite out of the box, leave `DATABASE_URL` as:
```
DATABASE_URL=sqlite+aiosqlite:///./livestockos.db
```

For PostgreSQL:
```
DATABASE_URL=postgresql+asyncpg://<username>:<password>@localhost:5432/livestockos
```

### 5. Run Database Migrations
Apply all schema migrations via Alembic:
```bash
alembic upgrade head
```

### 6. Populate Sample Seed Data
Populate demo farmers (Maria Garcia and Ramesh Patel), 14 cattle herd, sensors, readings, and alerts:
```bash
python seed.py
```

### 7. Start the Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running Automated Tests

Run the complete 24-test suite covering authentication, animal CRUD, sensor pairing, telemetry ingestion, alerts, and analytics:

```bash
pytest tests -v
```

---

## Pre-Seeded Demo Accounts

| Email | Password | Full Name | Farm Name |
| :--- | :--- | :--- | :--- |
| `maria@livestockos.io` | `password123` | Maria Garcia | Sunrise Dairy Farm (14 cattle, BLE sensors, alerts) |
| `ramesh@livestockos.io` | `password123` | Ramesh Patel | Green Valley Ranch |

---

## API Documentation & Contract

For the complete endpoint request and response specifications, refer to [CONTRACT.md](CONTRACT.md).
When the server is running, explore the live documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
