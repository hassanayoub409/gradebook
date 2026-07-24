# ==============================================================================
# Procfile — Gradebook deployment configuration
# ==============================================================================
#
# This file is only used once you actually deploy (e.g. to Render, Heroku, or
# any platform that reads a Procfile). It does nothing locally — `flask run`
# ignores this file completely. Safe to commit now and act on later.
#
# WHAT THIS FILE DOES:
#   web:      tells the platform how to start the app in production, using
#             Gunicorn instead of Flask's built-in dev server (which is not
#             safe/performant for production traffic).
#   release:  runs automatically on every deploy, BEFORE the new `web`
#             process starts. We use it to apply database migrations, so the
#             schema is always up to date before the new code goes live.
#
# ==============================================================================

web: gunicorn wsgi:app
release: flask db upgrade

# ==============================================================================
# FULL DEPLOYMENT RUNBOOK — read this when you're actually ready to deploy
# ==============================================================================
#
# ------------------------------------------------------------------------------
# STEP 0 — Decisions already made (documented here so you don't have to re-decide)
# ------------------------------------------------------------------------------
# Host:      Render (recommended) — free/cheap tier, GitHub push-to-deploy,
#            built-in managed PostgreSQL, no credit card needed to start.
#            Railway or Fly.io are fine alternatives; steps below are
#            Render-specific but the concepts transfer directly.
# Database:  SQLite (used locally) is NOT suitable for production — it can't
#            handle concurrent writes safely, and most hosts wipe the
#            filesystem on redeploy (which would silently delete your DB).
#            We switch to PostgreSQL in production; SQLite stays for local
#            dev, since DATABASE_URL is just an env var either way.
# Server:    Gunicorn replaces Flask's dev server for production traffic.
#
# ------------------------------------------------------------------------------
# STEP 1 — Add production dependencies (run these BEFORE deploying)
# ------------------------------------------------------------------------------
#   pip install gunicorn==22.0.0 psycopg2-binary==2.9.9
#   echo "gunicorn==22.0.0" >> requirements.txt
#   echo "psycopg2-binary==2.9.9" >> requirements.txt
#
# ------------------------------------------------------------------------------
# STEP 2 — Code change required: app/config.py
# ------------------------------------------------------------------------------
# Some platforms (Render included) hand you a DATABASE_URL starting with
# "postgres://", but SQLAlchemy 1.4+/2.x requires "postgresql://". Patch this
# at load time so it works regardless of which prefix the platform gives you.
#
# In the Config class, replace:
#
#     SQLALCHEMY_DATABASE_URI = os.environ.get(
#         "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "..", "gradebook.db")
#     )
#
# with:
#
#     _raw_db_url = os.environ.get(
#         "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "..", "gradebook.db")
#     )
#     if _raw_db_url.startswith("postgres://"):
#         _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
#     SQLALCHEMY_DATABASE_URI = _raw_db_url
#
# ------------------------------------------------------------------------------
# STEP 3 — Code change required: app/config.py (ProdConfig hardening)
# ------------------------------------------------------------------------------
# Confirm ProdConfig looks like this (some of these should already be present
# from the project skeleton stage — add whatever's missing):
#
#     class ProdConfig(Config):
#         DEBUG = False
#         SESSION_COOKIE_SECURE = True
#         REMEMBER_COOKIE_SECURE = True
#         SESSION_COOKIE_HTTPONLY = True
#         PREFERRED_URL_SCHEME = "https"
#
# ------------------------------------------------------------------------------
# STEP 4 — Confirm config selection mechanism (no code change, just verify)
# ------------------------------------------------------------------------------
# app/__init__.py's create_app() already reads:
#     config_name = config_name or os.environ.get("FLASK_ENV", "default")
# We just need to SET FLASK_ENV=production as an env var on the platform
# (see Step 8) — no code change needed here.
#
# ------------------------------------------------------------------------------
# STEP 5 — .gitignore sanity check (do this BEFORE pushing)
# ------------------------------------------------------------------------------
#   cat .gitignore
# Must include: .env, instance/, *.db
# You do NOT want to accidentally commit your local .env with real secrets.
# If any are missing, add them and commit that fix first.
#
# ------------------------------------------------------------------------------
# STEP 6 — Commit and push everything above to GitHub
# ------------------------------------------------------------------------------
#   git add Procfile app/config.py requirements.txt
#   git commit -m "Add production deployment config: Gunicorn, PostgreSQL support, hardened prod settings"
#   git push
#
# ------------------------------------------------------------------------------
# STEP 7 — Set up Render
# ------------------------------------------------------------------------------
#   1. Go to https://render.com, sign up/log in with GitHub.
#   2. New -> PostgreSQL -> create a database (free tier). Note the
#      "Internal Database URL" it gives you.
#   3. New -> Web Service -> connect your gradebook GitHub repo.
#   4. Configure:
#        Build command: pip install -r requirements.txt
#        Start command: leave blank (Render reads the Procfile's `web:` line
#                        automatically) — or explicitly set `gunicorn wsgi:app`
#                        if it doesn't pick it up.
#        Environment:   Python 3.
#
# ------------------------------------------------------------------------------
# STEP 8 — Environment variables to set in Render's dashboard
# ------------------------------------------------------------------------------
#   FLASK_ENV=production
#   SECRET_KEY=<generate a NEW one, do not reuse your local dev value>
#   DATABASE_URL=<paste the Internal Database URL from Step 7.2>
#   GOOGLE_CLIENT_ID=<your value>
#   GOOGLE_CLIENT_SECRET=<your value>
#
# Generate a fresh SECRET_KEY with:
#   python -c "import secrets; print(secrets.token_hex(32))"
#
# Then click Deploy. Render will:
#   a) run the build command
#   b) run the `release` step from this Procfile (flask db upgrade) to set
#      up/migrate your Postgres schema
#   c) start the `web` process (gunicorn wsgi:app)
#
# ------------------------------------------------------------------------------
# STEP 9 — Update Google Cloud Console for the production domain
# ------------------------------------------------------------------------------
# Once Render gives you your live URL (e.g. https://gradebook-xyz.onrender.com):
#   1. Go to Google Cloud Console -> your OAuth client.
#   2. Under Authorized redirect URIs, ADD (don't replace):
#        https://gradebook-xyz.onrender.com/login/google/callback
#   3. Keep the localhost one too — you'll still want it for local dev:
#        http://localhost:5000/login/google/callback
#
# ------------------------------------------------------------------------------
# STEP 10 — Bootstrap your first production admin
# ------------------------------------------------------------------------------
# From the Render dashboard -> your web service -> "Shell" tab, run:
#   flask create-admin
#
# (Use `flask seed-demo` only if you want to launch with demo/sample data —
# for a real deployment, `create-admin` is the right call so you're not
# shipping fake demo accounts publicly.)
#
# ------------------------------------------------------------------------------
# STEP 11 — Test the live deployment end to end
# ------------------------------------------------------------------------------
#   [ ] Signup: student gets immediate access; instructor/TA lands pending.
#   [ ] Admin login, approve a pending request, confirm that account can log in.
#   [ ] Google OAuth login — this is the step most likely to break on a fresh
#       deploy; double-check the redirect URI matches EXACTLY, including the
#       https:// scheme and no trailing slash mismatch.
#   [ ] Create a course, add sections/activities, enroll a student, enter marks.
#   [ ] Excel export downloads correctly (single course, all courses, roster).
#   [ ] CSV import works.
#   [ ] Confirm sessions/cookies persist correctly over HTTPS (stay logged in
#       across page loads/reloads).
#   [ ] Run through the unpublished-course visibility check (student shouldn't
#       see it; staff should).
#
# ------------------------------------------------------------------------------
# STEP 12 — Update README.md after a successful deploy
# ------------------------------------------------------------------------------
# Add/confirm a "Deployment" section documenting:
#   - Hosting platform used (Render)
#   - Required environment variables (table: FLASK_ENV, SECRET_KEY,
#     DATABASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
#   - Reminder to register the production OAuth redirect URI
#   - The `flask create-admin` bootstrap step for a fresh production DB
#
# ==============================================================================
# TROUBLESHOOTING — common first-deploy issues
# ==============================================================================
#
# "sqlalchemy.exc.OperationalError: could not connect to server"
#   -> DATABASE_URL is wrong, or you used the External URL instead of the
#      Internal Database URL (internal is faster and correct when the web
#      service and DB are on the same platform/region).
#
# "redirect_uri_mismatch" on Google login
#   -> The exact URL Flask generated doesn't match what's registered in
#      Google Cloud Console. Check for http vs https, trailing slashes, and
#      that PREFERRED_URL_SCHEME is set to "https" in ProdConfig so
#      url_for(..., _external=True) generates an https:// URL behind
#      Render's reverse proxy.
#
# Static files / CSS not loading
#   -> Confirm Bootstrap is still loaded via CDN (no local build step needed)
#      and that app/static/ files were actually committed to git (check
#      .gitignore isn't accidentally excluding them).
#
# "relation does not exist" errors on first load
#   -> The `release: flask db upgrade` step didn't run or failed silently.
#      Check the deploy logs in Render's dashboard for migration errors.
#
# App works but login doesn't persist / logs out immediately
#   -> SESSION_COOKIE_SECURE=True requires the connection to actually be
#      HTTPS. Render provides HTTPS automatically, but if you're testing via
#      a custom domain without SSL configured yet, cookies will silently
#      fail to set. Use the onrender.com URL first to confirm, then debug
#      the custom domain separately.
#
# ==============================================================================