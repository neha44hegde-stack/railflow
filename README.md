# RailFlow - Train Booking & Management System

A full-stack railway reservation system where passengers search trains, book tickets, and manage their journeys, while admins configure stations, routes, fares, and monitor operations through an analytics dashboard.

Every booking is a real database transaction - this is not a mockup.

---

## Features

### Passenger
- Register / Login with JWT authentication
- Search trains by source, destination, journey date, and class
- View route timeline, timings, seat availability, and distance-based fares
- Interactive **seat map** - available vs. booked seats at a glance
- Multi-passenger booking (up to 6 per transaction)
- Automatic seat allocation, concurrency-safe
- Real **PNR** generation (RF2026XXXXXX) linked to the booking
- **Waitlist (WL)** with automatic promotion when a confirmed seat cancels
- E-ticket with printable layout and **QR code**
- Booking history split into Upcoming / Completed / Cancelled
- Self-service cancellation with refund status tracking

### Admin
- **Dashboard KPIs** - trains, stations, users, bookings, revenue, waitlist
- **Analytics charts** (Recharts) - bookings per day, by class, popular trains, popular routes, revenue per train
- Stations CRUD
- Trains CRUD with activate/deactivate
- **Route management** - add/remove stops with arrival, departure, and distance in km
- Class & fare management per train (base fare, scaled by distance)
- All-bookings view with filters (PNR, status, journey date, train)
- User management with booking counts
- **Audit log** - every admin action recorded with timestamp, actor, entity, details

### Platform
- JWT authentication with role claims
- Role-based access control (PASSENGER, ADMIN) enforced on every protected route
- User isolation - a passenger can never see or cancel another passenger's booking
- Atomic booking transactions - full rollback on any failure
- Unique PNR generation with collision retry
- Distance-based fare: fare x (destination_km - source_km) / 100
- SQLite for dev, PostgreSQL-ready via DATABASE_URL

---

## Tech Stack

**Frontend**
- React 18 + Vite
- Tailwind CSS
- React Router
- Axios
- Lucide React
- Recharts (admin analytics only)

**Backend**
- Python 3.13
- Flask 3
- Flask-JWT-Extended
- Flask-SQLAlchemy
- Flask-CORS
- qrcode (ticket QR generation)

**Database**
- SQLite for local development
- PostgreSQL-ready via DATABASE_URL environment variable

**Testing**
- Pytest (auth, role checks, station CRUD, booking, cancellation, user isolation)

---

## Architecture

React (Vite) -> Axios -> Flask REST API -> SQLAlchemy -> SQLite / PostgreSQL

- Frontend and backend are separated projects.
- JWT stored in localStorage, sent as Authorization: Bearer <token>.
- The backend enforces authorization on every protected route.
- The frontend mirrors it with ProtectedRoute for UX only - the real check is server-side.

---

## Data Model

| Table | Purpose |
|---|---|
| users | Passengers and admins (hashed passwords) |
| stations | Name, unique code, city, state |
| trains | Train number, name, type, active status |
| train_stations | Route - stop order, arrival/departure, distance_km |
| train_classes | Per-train class, seat count, base fare, seat prefix |
| bookings | PNR, journey date, route, class, fare, status, booking_status, waitlist_position |
| passengers | Passenger name, age, gender, seat number |
| payments | Test-payment record per booking |
| audit_logs | Admin action history |

---

## Setup

### Prerequisites
- Python 3.13+
- Node.js 18+ and pnpm (npm install -g pnpm)
- PostgreSQL (optional - SQLite works by default)

### 1. Backend

    cd backend
    python -m venv .venv
    .venv\Scripts\activate          # Windows
    pip install -r requirements.txt
    python server.py                # http://localhost:5000

The API serves only /api/* - do not open it in a browser.

### 2. Frontend

In a second terminal:

    cd frontend
    pnpm install
    pnpm dev                        # http://localhost:5173

Open http://localhost:5173 in the browser.

### 3. Database

SQLite (default) - no setup needed. File lives at backend/instance/railflow_dev.db.

PostgreSQL (optional):

    docker compose up -d

Then create backend/.env with SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL.

### 4. Seed development data (optional)

    cd backend
    python seed.py

Creates 4 stations, 1 train with a 3-stop route, and 3 classes. Aborts safely if data already exists.

---

## API Overview

### Auth
- POST /api/auth/register
- POST /api/auth/login
- GET  /api/auth/me
- POST /api/auth/logout

### Stations
- GET / POST        /api/stations
- PUT / DELETE      /api/stations/<id>

### Trains
- GET / POST        /api/trains
- GET / PUT         /api/trains/<id>
- PATCH             /api/trains/<id>/status

### Routes
- GET / POST        /api/trains/<id>/route
- PUT / DELETE      /api/trains/<id>/route/<route_id>

### Classes
- GET / POST        /api/trains/<id>/classes
- PUT / DELETE      /api/trains/<id>/classes/<class_id>

### Search & Bookings
- GET  /api/trains/search
- POST /api/bookings
- GET  /api/bookings/my
- GET  /api/bookings/<id>
- POST /api/bookings/<id>/cancel
- GET  /api/bookings/seatmap

### PNR
- GET /api/pnr/<pnr>
- GET /api/pnr/<pnr>/qr

### Admin
- GET /api/admin/dashboard
- GET /api/admin/analytics
- GET /api/admin/bookings
- GET /api/admin/users
- GET /api/admin/audit

---

## Booking Flow

    Search train
       |
    Select class              (fares scale with distance)
       |
    Check availability        (live seat map)
       |
    Enter passenger details   (1-6 per booking)
       |
    Confirm (test payment)
       |
    Atomic transaction:
       - create booking row
       - allocate seat numbers
       - create passengers
       - create payment record
       |
    Return booking with PNR
       |
    Show ticket with QR code

If any step fails, the whole transaction rolls back - no orphan bookings, no double-booked seats.

---

## Running Tests

    cd backend
    pytest -v

Covers registration, login, role authorization, station CRUD, booking, cancellation, seat release, overbooking prevention, and cross-user isolation.

---

## Deployment

**Frontend -> Vercel**
- Root directory: frontend
- Build: pnpm install && pnpm build
- Env: VITE_API_URL=https://your-backend.onrender.com/api

**Backend -> Render**
- Root directory: backend
- Build: pip install -r requirements.txt
- Start: gunicorn "app:create_app()"
- Env: DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY

**Database -> Neon / Supabase / Render PostgreSQL (free tier)**

---

## Notes

- Payment is a **test-only** flow. No real gateway is integrated. Every booking writes a payment row with status SUCCESS to simulate a paid transaction.
- The e-ticket is **not** a valid Indian Railways ticket - it is a demo.
- Built without unnecessary dependencies: no ML, no AI, no crypto, no bloat.

---

## License

MIT
## Live demo
https://drive.google.com/file/d/1LVCxqjN6YEtHuN8HZP4FfUL5jabwRnCs/view?usp=drive_link




