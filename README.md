# Gradebook

A Flask-based course results platform for students, instructors, TAs, and admins to manage
and view quiz/assignment/midterm/final marks.

## Status

Under active development. Currently at: **Stage 11 — automated test suite**.

## Tech Stack

- Flask 3 (application factory + blueprints)
- Flask-SQLAlchemy / Flask-Migrate
- Flask-Login, Flask-Bcrypt
- Flask-WTF (CSRF)
- Authlib (Google OAuth)

## Roles

| Role | Capabilities |
|---|---|
| Student | View enrolled courses/marks, export own results. Immediate signup, no approval. |
| Instructor / TA | Manage courses, sections, activities, enrollments, marks. Signup requires admin approval. |
| Admin | Approves/rejects/direct-creates instructor, TA, and admin accounts. Does not manage courses. |

## Out of Scope

Grading rubrics, plagiarism detection, real-time chat, mobile app, multi-tenant institutions —
kept out by design to stay a scoped personal project.

## Known Limitations

1. If a registrations request (for Instructor/Admin/TA account) is rejected, the details of registration
such as email, username etc. are stored in the database for audit trail. This means the same username or email
cannot be used for any future registrations.

2. It is not enforced that section (quizzes, assignments, ...) weights add up to 100. It is left for instructors/TAs
to make sure according to the logistics at hand.

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

## Demo Data

Run `flask seed-demo` to populate the database with a realistic demo dataset (2 courses,
staff, students, marks, and pending requests). All demo accounts use password `password123`.
See the command's output for the full account list.

## Project Structure

See `app/` — application factory in `app/__init__.py`, blueprints per feature area
(`auth`, `admin`, `main`, `courses`, `exports`), models in `app/models/`.

## Roadmap

- [x] Project skeleton, config, placeholder landing page
- [x] User model + local signup/login (student ungated; instructor/TA/admin gated, pending review)
- [x] Admin approval workflow + CLI bootstrap (`flask create-admin`)
- [x] Course model + staff course creation + student/staff dashboards
- [x] Section/Activity models + staff CRUD
- [x] Mark model + manual entry + student totals
- [x] Student enrollment
- [x] Excel export
- [x] CSV mark import
- [x] Google OAuth login
- [x] Tests (auth, permissions, exports)
- [ ] Deployment