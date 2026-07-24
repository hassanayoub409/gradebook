# Gradebook

A Flask-based course results platform for students, instructors, TAs, and admins to manage
and view quiz/assignment/midterm/final marks.

![Language](https://img.shields.io/badge/Language-Python%203.11-blue)
![Framework](https://img.shields.io/badge/Framework-Flask%203-green)
![Frontend](https://img.shields.io/badge/Frontend-Bootstrap%205-purple)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-lightgrey)

---

## Features

- **Role-based access** — Student, Instructor, TA, and Admin, each with distinct permissions
- **Admin approval workflow** — Instructor/TA/Admin signups are gated behind admin review;
  students get immediate access
- **Course management** — Instructors/TAs create courses, sections, and activities; multiple
  staff can co-manage a course
- **Draft/publish gating** — Unpublished courses stay fully hidden from students, even if enrolled
- **Student enrollment** — Direct enrollment by email, or pending invitations that auto-convert
  the moment an invited email signs up
- **Marks management** — Manual entry grid or bulk CSV import, with all-or-nothing validation
- **Grading engine** — Weighted section/course totals, with ungraded work conservatively
  counted as zero
- **Excel export** — Students export their own results (single course or all courses); staff
  export a full course roster/gradebook
- **Google OAuth login** — Account linking with existing local accounts, new-user role selection
- **Automated test suite** — Auth, admin workflow, course permissions, and export access control

---

## Roles

| Role | Capabilities |
|---|---|
| **Student** | View enrolled (published) courses, view sections/activities/marks, export own results to Excel. Signup is immediate — no approval needed. |
| **Instructor** | Everything a TA can do (identical permission set). Signup creates a pending request; cannot log in until an Admin approves it. |
| **TA** | Create courses, create sections, create activities, enroll students, enter/import marks, edit/delete anything inside their courses, add/remove co-staff. Signup creates a pending request; cannot log in until an Admin approves it. |
| **Admin** | Approves or rejects instructor/TA/Admin signup requests, or creates any of those three roles directly. Does not manage courses, sections, activities, or marks — out of scope for the Admin role. |

**Out of scope (by design):** grading rubrics, plagiarism detection, real-time chat, mobile app,
multi-tenant institutions.

---

## Tech Stack

- **Backend:** Flask 3 (application factory + blueprints)
- **Database:** Flask-SQLAlchemy / Flask-Migrate — PostgreSQL in production, SQLite for local dev
- **Auth:** Flask-Login, Flask-Bcrypt, Authlib (Google OAuth)
- **Forms/Security:** Flask-WTF (CSRF protection)
- **Frontend:** Bootstrap 5 (CDN)
- **Exports:** openpyxl (Excel generation)
- **Testing:** pytest

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | `python3 --version` |
| pip | Comes with Python |
| Google Cloud project | Only needed if testing Google OAuth locally |

---

## Local Setup

1. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

2. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

3. Install the project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create your environment file:

   ```bash
   cp .env.example .env
   ```

   Open `.env` and set `SECRET_KEY`, `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`.

5. Set up the database:

   ```bash
   flask db upgrade
   ```

6. Create your first account. Either:

   - **A single admin account**, to start from a clean slate:

     ```bash
     flask create-admin
     ```

   - **Or a full demo dataset** (admin, instructors, TAs, students, two courses with marks,
     and pending requests) — useful for quickly exploring the app:

     ```bash
     flask seed-demo
     ```

7. Run the application:

   ```bash
   flask run
   ```

Google OAuth requires a project in Google Cloud Console with an OAuth client (Web application),
redirect URI `http://localhost:5000/login/google/callback` for local dev.

---

## Demo Data

Run `flask seed-demo` to populate the database with a realistic demo dataset (2 courses,
staff, students, marks, and pending requests). All demo accounts use password `password123`.
See the command's output for the full account list.

---

## Running Tests

```bash
pytest -v
```

Tests use an in-memory SQLite database and cover auth (signup/login gating), admin
(approve/reject/direct-create/last-admin protection), course permissions and grading
math, and export access control.

---

## Project Structure

```
gradebook/
├── app/
│   ├── __init__.py              # create_app() factory, extension init, CLI commands registered here
│   ├── config.py                # Config, DevConfig, ProdConfig, TestConfig
│   ├── extensions.py            # db, login_manager, bcrypt, migrate, oauth, csrf instantiated here
│   ├── cli.py                   # flask create-admin, flask seed-demo
│   ├── models/
│   │   ├── user.py              # User model, RoleEnum, ApprovalStatusEnum
│   │   ├── course.py            # Course, CourseStaff, Enrollment, PendingEnrollment
│   │   └── academic.py          # Section, Activity, Mark
│   ├── auth/                    # Local + Google OAuth signup/login
│   ├── admin/                   # Approve/reject/direct-create/remove gated-role accounts
│   ├── main/                    # Landing page, role-based dashboard routing
│   ├── courses/                 # Course/section/activity/enrollment/staff/marks CRUD
│   ├── exports/                 # Excel export (student results + staff roster)
│   ├── templates/                # Jinja templates, mirrors blueprint structure
│   ├── static/
│   │   ├── css/theme.css        # Bootstrap overrides
│   │   └── img/
│   └── utils/
│       ├── grades.py             # Weighted grading calculations
│       ├── csv_import.py         # CSV marks parsing/validation
│       └── validators.py         # Shared validation helpers
├── migrations/                   # Flask-Migrate revisions
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_admin.py
│   ├── test_courses.py
│   └── test_exports.py
├── Procfile                      # Gunicorn + release migration step, for deployment
├── .env.example
├── .flaskenv
├── .gitignore
├── requirements.txt
├── wsgi.py                       # Entry point: from app import create_app; app = create_app()
└── README.md
```

---

## Known Limitations

- Rejected instructor/TA/admin signup requests permanently hold their username and email —
  that person cannot sign up again with the same details.
- Course-total percentage counts any ungraded section as 0 — it's a conservative "your grade
  if nothing else gets graded" figure, not a projection of final performance. This means the
  percentage will only go up as more gets graded, never down.
- Courses are hidden from students entirely (dashboard and direct URL) while `is_published`
  is false, even if the student is enrolled — course staff always retain full access
  regardless of publish state.
- Admin has no course dashboard — logging in or visiting `/dashboard` redirects straight to
  `/admin/requests`, since course management is out of scope for the Admin role.
---

## Author

**Hassan Ayoub** - 2026

---

## License
![License](https://img.shields.io/badge/License-MIT-yellow)
This project is for educational and personal use. 

**This project was vibe-coded with Claude.**