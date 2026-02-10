# AutoDesk Kiwi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)

> A self-hosted personal productivity dashboard that centralizes tasks, calendar, weather, email and daily essentials in a single interface.

---

## Overview

AutoDesk Kiwi is a full-stack productivity application built with FastAPI and Alpine.js. It provides a unified workspace for managing tasks, tracking habits, viewing school schedules (Hyperplanning), checking weather, and monitoring email — all from a responsive dark-themed web interface.

**Key principles:**
- **Privacy-first** — Self-hosted with local SQLite database
- **Lightweight** — No build step required, pure HTML/CSS/JS frontend
- **Extensible** — REST API with Swagger documentation
- **Secure** — JWT authentication, rate limiting, SSRF protection, XSS sanitization

---

## Features

### Task Management
- Full CRUD with priority levels (low, normal, high) and status tracking (todo, doing, done, archived)
- Kanban board and list views with drag-and-drop
- Subtasks, recurring tasks (daily/weekly/monthly), colored tags
- Advanced filtering, sorting, and full-text search
- Bulk operations and PDF export

### Productivity Tools
- Pomodoro timer with browser notifications and session tracking
- Habit tracker with 7-day grid and streak tracking
- Gamification system with XP, levels, badges, and daily streaks
- Analytics dashboard with Chart.js visualizations (daily/weekly trends, status/priority distribution)

### Integrations
- **Hyperplanning** — iCalendar parsing for class schedules, grade import, subject statistics
- **Weather** — Real-time forecasts via Open-Meteo with geolocation
- **Proton Mail** — IMAP inbox integration via Proton Bridge
- **Spotify** — Now playing, playback controls, recent tracks

### Interface
- Dark/light/auto theme with 8 accent color options
- Focus mode for distraction-free work
- Keyboard shortcuts (`Ctrl+1-6` navigation, `Ctrl+N` new task, `?` help)
- PWA support with offline caching via service worker
- Responsive design for desktop and mobile

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) with Python 3.12+ |
| Database | SQLite via [SQLModel](https://sqlmodel.tiangolo.com/) ORM |
| Frontend | [Alpine.js](https://alpinejs.dev/) + vanilla CSS |
| Charts | [Chart.js](https://www.chartjs.org/) |
| Auth | JWT (python-jose) + bcrypt |
| Security | DOMPurify, slowapi rate limiting, SSRF whitelist |
| DevOps | Docker, Docker Compose |

---

## Installation

### Prerequisites

- Python 3.12+
- Modern web browser

### Setup

```bash
git clone https://github.com/Kiwi6212/autodesk_kiwi.git
cd autodesk_kiwi/api

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your configuration, then start the server:

```bash
python main.py
```

The application is available at `http://127.0.0.1:8000`.

- API documentation: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Docker

```bash
docker compose up -d
```

---

## Project Structure

```
autodesk_kiwi/
├── api/
│   ├── routes/
│   │   ├── tasks.py           # Task CRUD and filtering
│   │   ├── analytics.py       # Productivity statistics
│   │   ├── hyperplanning.py   # Schedule and grades
│   │   ├── integrations.py    # Weather and geocoding
│   │   ├── email.py           # Proton Mail integration
│   │   ├── spotify.py         # Spotify playback
│   │   └── meta.py            # Health check and overview
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_tasks.py
│   │   └── test_meta.py
│   ├── main.py                # Application entry point
│   ├── models.py              # SQLModel schemas
│   ├── auth.py                # JWT authentication
│   ├── db.py                  # Database session management
│   ├── config.py              # Settings (pydantic-settings)
│   ├── logger.py              # Colored console logging
│   ├── exceptions.py          # Custom exception handlers
│   └── requirements.txt
├── web/
│   ├── index.html             # Single-page application
│   ├── app.js                 # Alpine.js application logic
│   ├── style.css              # Theme and responsive styles
│   ├── sw.js                  # Service worker (PWA)
│   └── manifest.json          # PWA manifest
├── docs/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Create user account |
| `/auth/login` | POST | Authenticate, returns JWT |
| `/auth/me` | GET | Current user info |
| `/tasks` | GET | List tasks (filterable, sortable) |
| `/tasks` | POST | Create task |
| `/tasks/{id}` | PUT | Update task |
| `/tasks/{id}` | DELETE | Delete task with subtasks |
| `/tasks/bulk-delete` | POST | Bulk delete |
| `/tasks/stats/summary` | GET | Task statistics |
| `/analytics/tasks/daily` | GET | Daily completion stats |
| `/analytics/productivity/summary` | GET | Productivity summary |
| `/hyperplanning/courses` | GET | Today's schedule |
| `/hyperplanning/grades` | GET | All grades |
| `/external/weather` | GET | Current weather |
| `/external/forecast` | GET | Hourly/daily forecast |
| `/spotify/now-playing` | GET | Current track |
| `/email/proton/unread` | GET | Unread emails |

Full interactive documentation available at `/docs` when running.

---

## Security

- **Authentication**: JWT tokens with bcrypt password hashing and configurable expiration
- **Rate limiting**: Per-IP throttling via slowapi (default 60 req/min, auth endpoints stricter)
- **SSRF protection**: Domain whitelist for external calendar URLs
- **XSS prevention**: DOMPurify sanitization on all HTML content
- **Security headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy
- **Input validation**: Pydantic models on all API inputs
- **Error handling**: Generic error messages to prevent information leakage

---

## Testing

```bash
cd api
pytest tests/ -v
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

Copyright (c) 2025 Mathias Quillateau

---

## Contact

**Mathias Quillateau** — [@Kiwi6212](https://github.com/Kiwi6212)
