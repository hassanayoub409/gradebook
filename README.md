# Gradebook

A Flask-based course results platform for students, instructors, TAs, and admins to manage
and view quiz/assignment/midterm/final marks.

## Status

Under active development. Currently at: **Stage 7 — Excel export**.

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

   Open `.env` and set a secure `SECRET_KEY`.

5. Run the application:

   ```bash
   flask run
   ```

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
- [ ] CSV mark import
- [ ] Google OAuth login
- [ ] Tests (auth, permissions, exports)
- [ ] Deployment