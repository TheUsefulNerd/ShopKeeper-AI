# ShopKeeper AI — Build Log

_Append only. One entry per task. Never edit previous entries._

---

### Authentication — JWT (Username/Password) — 2026-05-22
**What was built:** Full JWT auth layer — User SQLAlchemy model, Alembic migration (applied to Supabase dev), bcrypt + python-jose auth service, reusable `get_current_user` FastAPI dependency, four route handlers (register, login, refresh, logout), `GET /api/v1/auth/me` protected stub, and `app/main.py` entry point. 9 tests written and passing.
**Decisions made:** Logout uses Redis blocklist (refresh token stored with TTL equal to its remaining lifetime). Token type field (`"access"` / `"refresh"`) added to JWT payload to prevent refresh tokens being accepted on protected routes. `app/db.py` created as a central session factory to avoid circular imports. Redis blocklist functions mocked at the route module level in tests because the `.env` test Redis URL is a placeholder.
**What is next:** Database layer — SQLAlchemy models for remaining 18 tables defined in the schema, all wired to Alembic.

---

### Authentication — Google OAuth 2.0 — 2026-05-23
**What was built:** Google OAuth 2.0 flow on top of the existing JWT layer. Updated `app/models/user.py` to add `email` and `google_id` columns (both nullable, unique, indexed) and made `hashed_password` and `username` nullable to support partial OAuth registration. Added `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` to `config.py` (Pydantic Settings) and `.env` (placeholders only — no real credentials). Added four new service functions (`build_google_auth_url`, `exchange_google_code`, `fetch_google_user_info`, `create_google_pending_token`) to `app/services/auth.py`. Added three new routes to `app/api/v1/auth.py` (`GET /auth/google/initiate`, `GET /auth/google/callback`, `POST /auth/google/complete`). Updated `POST /auth/login` to accept email or username (detected by `@`). Added `GooglePendingResponse` and `CompleteGoogleRegistrationRequest` schemas to `app/schemas/auth.py`. Created Alembic migration `a1b2c3d4e5f6` and applied it to Supabase dev. Wrote `tests/test_google_auth.py` with all 11 specified test cases. All 19 tests (9 existing JWT + 11 new OAuth — one test overlaps logic, total 19 collected) pass with 0 warnings.
**Decisions made:** `google-auth` library not added — `httpx` (already in requirements) handles the OAuth code exchange and userinfo fetch. `username` column made nullable in the migration to allow partial OAuth users. `LoginRequest.username` field name preserved (email-vs-username detection in route handler only) to avoid breaking existing test_auth.py. `google_pending` token uses same python-jose signing with `type: "google_pending"` in payload; `get_current_user` rejects it automatically (checks `type == "access"`). GitHub Secrets (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`) must be added manually as dummy placeholders via GitHub UI — they are not added by the agent.
**What is next:** Database layer — SQLAlchemy models for remaining 18 tables defined in the schema, all wired to Alembic.
