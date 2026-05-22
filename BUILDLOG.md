# ShopKeeper AI — Build Log

_Append only. One entry per task. Never edit previous entries._

---

### Authentication — JWT (Username/Password) — 2026-05-22
**What was built:** Full JWT auth layer — User SQLAlchemy model, Alembic migration (applied to Supabase dev), bcrypt + python-jose auth service, reusable `get_current_user` FastAPI dependency, four route handlers (register, login, refresh, logout), `GET /api/v1/auth/me` protected stub, and `app/main.py` entry point. 9 tests written and passing.
**Decisions made:** Logout uses Redis blocklist (refresh token stored with TTL equal to its remaining lifetime). Token type field (`"access"` / `"refresh"`) added to JWT payload to prevent refresh tokens being accepted on protected routes. `app/db.py` created as a central session factory to avoid circular imports. Redis blocklist functions mocked at the route module level in tests because the `.env` test Redis URL is a placeholder.
**What is next:** Database layer — SQLAlchemy models for remaining 18 tables defined in the schema, all wired to Alembic.