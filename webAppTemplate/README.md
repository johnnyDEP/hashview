# Web Application Template (Nemesis-Inspired)

This project is a modern, containerized web application skeleton inspired by the architecture and design of [SpecterOps/Nemesis](https://github.com/SpecterOps/Nemesis), but fully generic and stripped of project-specific logic. It features a Python FastAPI backend and a React + Material UI frontend, ready for rapid development of data-driven dashboards and management tools and can be a basic start to merge with any CLI tool that you want to covert into a web application with an api etc.

---

## Project Structure

```
webAppTemplate/
├── backend/      # FastAPI backend (Python)
├── frontend/     # React + Material UI frontend (Vite)
├── infra/        # Infrastructure as code (Docker Compose, etc.)
├── docs/         # Documentation and guides
└── README.md     # Project overview (this file)
```

---

## Features
- **JWT-based authentication** (register, login, protected endpoints)
- **User management** (in-memory, extensible)
- **Placeholder data models and endpoints** for files, analytics, and system status
- **Nemesis-inspired dashboard UI** (React + Material UI, dark mode, sidebar navigation)
- **Containerized** for local or cloud deployment (Docker Compose, Nginx reverse proxy)
- **Extensible**: add your own logic, models, and UI components

---

## Quick Start

### Prerequisites
- Docker & Docker Compose (or Podman)
- Node.js (for local frontend dev)
- Python 3.9+ (for local backend dev)

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd webAppTemplate
```

### 2. Local Development (with Docker Compose)
```sh
docker compose -f infra/docker-compose.yaml up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### 3. Local Development (separately)
#### Backend
```sh
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
#### Frontend
```sh
cd frontend
npm install
npm run dev
```

---

## Authentication Flow
- Register or login at `/login` (frontend)
- JWT token is stored in localStorage and sent with API requests
- Protected API endpoints require a valid token

---

## API Endpoints (Backend)
- `POST   /api/register` — Register a new user
- `POST   /api/login` — Obtain JWT token
- `GET    /api/users` — List users (auth required)
- `GET    /api/files` — List files (auth required)
- `GET    /api/analytics` — Analytics summary (auth required)
- `GET    /api/system_status` — System status (auth required)

---

## Customization
- **Backend**: Add models, endpoints, and business logic in `backend/app.py`
- **Frontend**: Add pages/components in `frontend/src/`, update routes in `App.jsx`
- **Infra**: Update `infra/docker-compose.yaml` for services, volumes, and networking

---

## Notes
- This template is intentionally generic—no business logic or branding is included.
- The frontend uses a relative `/api` path and expects the backend to be reverse-proxied (see Nginx config in Docker setup).
- For production, update secrets and use persistent storage for users/data.

---

## License
MIT or your preferred license. 
