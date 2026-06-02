# Trackify — HRMS Backend API

![Python](https://img.shields.io/badge/Python-3.12.4-blue?style=flat-square)
![Django](https://img.shields.io/badge/Django-6.0-green?style=flat-square)
![DRF](https://img.shields.io/badge/DRF-3.16.1-red?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue?style=flat-square)
![JWT](https://img.shields.io/badge/Auth-JWT-orange?style=flat-square)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-72%20Passing-brightgreen?style=flat-square)

A production-ready **Human Resource Management System** built with Django and Django REST Framework. Trackify handles employee management, project allocations, attendance tracking, and leave management with a robust role-based access control system.

---

## Live Demo

- **API Base URL:** https://trackify-cie8.onrender.com/
- **Swagger UI:** https://trackify-cie8.onrender.com/api/docs/
- **ReDoc:** https://trackify-cie8.onrender.com/api/redoc/

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0, Django REST Framework |
| Authentication | JWT via djangorestframework-simplejwt |
| Database | PostgreSQL (Neon) |
| API Documentation | drf-yasg (Swagger UI + ReDoc) |
| Filtering | django-filter |
| Deployment | Render |
| Static Files | Whitenoise |
| Testing | Django Test Framework |

---

## Features

- **JWT Authentication** — Secure login with access and refresh tokens, token blacklisting on logout
- **Role Based Access Control (RBAC)** — Four roles with distinct permissions: Global HR, Project HR, Supervisor, and Employee
- **Employee Management** — Full CRUD with role-based restrictions on create, update, and delete
- **Project Management** — Create and manage billable and non-billable projects with HR assignments
- **Project Membership** — Track employee allocations, roles, and durations across projects
- **Attendance Tracking** — Daily attendance with check-in/check-out, cross-referenced with leaves and holidays
- **Leave Management** — Apply, approve, and reject leaves with quota tracking (EL, CL, SL, OL)
- **Holiday Management** — National, regional, and flexi holiday support
- **Pagination** — All list endpoints paginated with 10 records per page
- **Filtering and Search** — Filter and search across employees, projects, and memberships
- **Swagger Documentation** — Full interactive API documentation with request/response descriptions
- **72 Automated Tests** — Comprehensive test coverage across all apps

---

## Role Permissions

| Role | Permissions |
|---|---|
| **Global HR** | Full system access — create employees, projects, view all data |
| **Project HR** | Manage their own projects, allocate employees, approve leaves |
| **Supervisor** | View and manage employees under their supervision |
| **Employee** | View and manage only their own records |

---

## Project Structure

```
Trackify/
├── accounts/               # Employee model, JWT auth, custom user manager
├── attendance/             # Daily attendance tracking
├── common/                 # Shared base models
├── core/                   # Project settings and root URLs
├── leaves/                 # Leave applications and quota management
├── organization/           # Holiday management
├── projects/               # Project and membership management
├── manage.py
├── requirements.txt
└── Procfile
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/api/accounts/login/` | Login and get JWT tokens | Public |
| POST | `/api/accounts/logout/` | Logout and blacklist token | Authenticated |
| POST | `/api/token/refresh/` | Refresh access token | Authenticated |

### Employees
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/accounts/employees/` | List all employees | Authenticated |
| POST | `/api/accounts/employees/` | Create employee | Global HR |
| GET | `/api/accounts/employees/{id}/` | Get employee details | Authenticated |
| PUT/PATCH | `/api/accounts/employees/{id}/` | Update employee | Global HR or Self |
| DELETE | `/api/accounts/employees/{id}/` | Delete employee | Global HR |

### Projects
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/projects/projects/` | List all projects | Authenticated |
| POST | `/api/projects/projects/` | Create project | Project HR |
| GET | `/api/projects/projects/{id}/` | Get project details | Authenticated |
| PUT/PATCH | `/api/projects/projects/{id}/` | Update project | Project HR |
| DELETE | `/api/projects/projects/{id}/` | Delete project | Project HR |

### Project Memberships
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/projects/memberships/` | List memberships | Role-based |
| POST | `/api/projects/memberships/` | Assign employee to project | Project HR or Global HR |
| PATCH | `/api/projects/memberships/{id}/` | Update membership | Project HR or Global HR |
| DELETE | `/api/projects/memberships/{id}/` | Remove membership | Project HR or Global HR |

### Attendance
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/attendance/monthly/` | Get monthly attendance | Role-based |
| POST | `/api/attendance/create/` | Mark attendance | Role-based |

### Leaves
| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/api/leaves/apply/` | Apply for leave | Employee |
| GET | `/api/leaves/my/` | View own leaves | Employee |
| PATCH | `/api/leaves/{id}/action/` | Approve or reject leave | HR roles |
| GET | `/api/leaves/balance/` | View leave balance | Employee |
| GET | `/api/leaves/team/` | View team leaves | HR roles |
| GET | `/api/leaves/today/` | Who is on leave today | All roles |
| GET | `/api/leaves/calendar/` | Monthly leave calendar | All roles |

---

## Local Setup

### Prerequisites
- Python 3.12.4
- PostgreSQL or use SQLite for local development

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/sd-cnd/Trackify
cd Trackify
```

**2. Create and activate virtual environment**
```bash
python -m venv env
source env/bin/activate        # Mac/Linux
env\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create `.env` file in project root**
```
SECRET_KEY=your_secret_key_here
DEBUG=True
DATABASE_URL=your_postgresql_connection_string
```

**5. Run migrations**
```bash
python manage.py migrate
```

**6. Create superuser**
```bash
python manage.py createsuperuser
```

**7. Run the development server**
```bash
python manage.py runserver
```

**8. Visit Swagger UI**
```
http://127.0.0.1:8000/api/docs/
```

---

## Running Tests

```bash
python manage.py test
```

Expected output:
```
Ran 72 tests in Xs
OK
```

---

## How to Use the API

**Step 1 — Login**

Send a POST request to `/api/accounts/login/` with:
```json
{
    "email": "your@email.com",
    "password": "yourpassword"
}
```

**Step 2 — Copy the access token from response**
```json
{
    "access": "eyJ...",
    "refresh": "eyJ...",
    "role": "GLOBAL_HR"
}
```

**Step 3 — Authorize in Swagger UI**

Click the **Authorize** button and enter:
```
Bearer eyJ...your_access_token
```

**Step 4 — Use any endpoint**

All endpoints are now accessible based on your role.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | True for development, False for production |
| `DATABASE_URL` | PostgreSQL connection string |

---

## Database Schema

| Model | Description |
|---|---|
| `Employee` | Custom user model with role-based access |
| `Project` | Project with type, HR, and supervisor |
| `ProjectMembership` | Employee-project allocation with role and duration |
| `Attendance` | Daily attendance with check-in/check-out |
| `LeaveQuota` | Yearly leave limits per employee |
| `Leave` | Leave applications with status and approver |
| `Holiday` | National, regional, and flexi holidays |

## Entity Relationship Diagram

<p align="center">
  <img src="https://i.ibb.co/TMsFpb9x/ER-Diagram-Trackify.png" width="700" height="700"/>
</p>

**Constraints:**
- Only one active ProjectMembership per employee (end_date IS NULL)
- Attendance is unique per (employee, date)
- LeaveQuota is unique per (employee, year)

### Key Relationships

- `Employee` is the central model — almost every other model has a foreign key to it
- `Project` has three Employee foreign keys — supervisor, HR, and created_by
- `ProjectMembership` links Employee and Project with a unique constraint — only one active membership per employee at a time
- `Attendance` is linked to both Employee and Project — tracks which employee worked on which project on a given day
- `Leave` has two Employee foreign keys — one for the applicant and one for the approver
- `LeaveQuota` tracks yearly leave limits and taken leaves per employee per year
- `Holiday` affects attendance status — a day marked as a holiday shows as HOLIDAY in attendance records

---

## Author

**Sumit Dey**
- GitHub: [sd-cnd](https://github.com/sd-cnd)
- Live API: [Trackify on Render](https://trackify-cie8.onrender.com/)