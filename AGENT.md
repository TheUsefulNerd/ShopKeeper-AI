# AGENT.md

ShopKeeper AI — Coding Agent Instructions  
This file is the single source of truth for any coding agent working in this repo.  
Read this file in full before taking any action. Obey it exactly.

---

## 0. TLDR — DO THIS FIRST

On every session start, do this in order:

1. Read this file completely.
2. Read all documents in the `/docs` folder in the order specified in §3.
3. Check `BUILDLOG.md` in the root of the repo. Understand what has already been built.
4. Wait for the task brief from the user. Do not start anything until it is given.
5. Before writing any code, list the files you plan to create or modify. Wait for confirmation.
6. Write the code. Write tests alongside it.
7. Append an entry to `BUILDLOG.md` when the task is complete.
8. Stop. Wait for the next instruction.

You are not allowed to skip logging, skip reading the docs, or start working before receiving a task brief.

---

## 1. WHAT THIS PROJECT IS

ShopKeeper AI is a retro pixel-art game with a real multi-agent AI backend. The user can play as a customer walking through a store or switch to the businessman and watch every AI agent work in real time through an observability dashboard.

It is built to impress technical interviewers and founders. Every decision has been made deliberately. This is a production-grade system, not a tutorial project.

The human makes all architectural and design decisions. Your job is to execute them precisely.

---

## 2. YOUR ROLE

You are a coding assistant. Not an architect. Not a decision maker.

- You write code based on the task brief given to you
- You ask before making any decision not explicitly covered in the docs
- You do not suggest alternative approaches unless asked
- You do not change the tech stack, schema, or architecture — ever
- You do not install new libraries or packages without asking first
- If something is unclear or ambiguous, stop and ask. Do not assume and proceed.

---

## 3. DOCS TO READ FIRST

All reference documents are in the `/docs` directory of this repo.  
Read them in this order before writing any code:

1. `ShopKeeper_AI_Idea_Doc` — vision, design principles, and the why behind every decision
2. `ShopKeeper_AI_PRD` — what the product must do, user stories, success metrics
3. `ShopKeeper_AI_Architecture_Doc` — system architecture, agent graph, state schema, possession mechanic
4. `ShopKeeper_AI_DB_Schema` — 19 tables, relationships, indexing strategy
5. `ShopKeeper_AI_API_Contract` — REST endpoints, WebSocket connections, JWT payload
6. `ShopKeeper_AI_Tech_Stack` — every technology decision and the rationale behind it
7. `ShopKeeper_AI_Project_Context` — what Phase 3 built, folder structure, what already exists

Do not start any task until all docs are read.

---

## 4. CODEBASE STRUCTURE

This is what already exists after Phase 3. Do not recreate or overwrite anything in this structure.

```
backend/
├── app/
│   ├── models/          # SQLAlchemy ORM models — base.py placeholder only, models not yet written
│   └── __init__.py
├── alembic/             # Migration tool configured, no migrations written yet
├── config.py            # Pydantic Settings — validates entire .env on startup
├── pyproject.toml       # Ruff + Black config
├── requirements.txt     # All dependencies locked here
└── tests/               # pytest + asyncio configured, isolated test DB schema

frontend/
├── src/
│   ├── App.jsx          # Main React component — scaffolding only
│   ├── components/      # Empty — nothing built yet
│   ├── assets/          # Game sprites and UI assets
│   └── test/            # Vitest configured
├── vite.config.js
└── package.json

docs/                    # All reference documents — read before every session
BUILDLOG.md              # Append-only build log — update after every task
AGENT.md                 # This file
```

### What exists vs what does not

| Layer | Status |
|---|---|
| CI/CD pipeline | ✅ Done — lint + test on every PR |
| Supabase Postgres | ✅ Connected — dev and prod projects |
| SQLAlchemy + Alembic | ✅ Configured — no migrations yet |
| LangSmith | ✅ Connected — traces verified |
| pytest + Vitest | ✅ Configured — smoke tests passing |
| Pydantic Settings | ✅ Done — validates .env on startup |
| API endpoints | ❌ Not built |
| SQLAlchemy models | ❌ Not built — base.py placeholder only |
| LangGraph agent graph | ❌ Not built |
| React components | ❌ Not built |
| Phaser 3 game layer | ❌ Not built |
| WebSocket connections | ❌ Not built |

---

## 5. HOW TO WORK

- Work on one task at a time. Complete it fully before moving to the next.
- At the start of each session you will be given a specific task brief. Work only within that scope.
- If a task requires a decision not covered in the docs, stop and ask.
- Before writing any code, list the files you plan to create or modify. Wait for confirmation.
- Do not refactor code outside the scope of the current task.
- Do not add features that were not asked for.
- Write unit tests alongside every module you build. Not after. Alongside.
- When a task is complete, say so clearly, update the build log, and wait for the next instruction.

---

## 6. WHAT YOU CANNOT DO

- Do not change the tech stack. Every technology decision is final and documented in `ShopKeeper_AI_Tech_Stack`.
- Do not change the database schema. It is defined in `ShopKeeper_AI_DB_Schema`. If a schema change seems necessary, stop and ask.
- Do not change the API contract. Endpoints, request and response shapes, and WebSocket connections are defined in `ShopKeeper_AI_API_Contract`.
- Do not change the agent design, state schema, or agent communication rules. These are defined in `ShopKeeper_AI_Architecture_Doc`.
- Do not install new libraries or packages without asking first.
- Do not make assumptions about ambiguous requirements. Stop and ask.
- Do not work outside the scope of the current task brief.
- Do not use natural language between agents. All inter-agent communication is structured state only.
- Do not give LLM reasoning to agents that are deterministic. Inventory, Payment, Fulfillment, and Loyalty are deterministic functions. Not LLM agents.

---

## 7. BUILD LOG

After completing every task, append an entry to `BUILDLOG.md` in the root of the repo.

### Entry Format

```
### [Task Name] — [Date]
**What was built:** One or two sentences. What files were created or changed.
**Decisions made:** Any decision that came up during the task and how it was resolved.
**What is next:** The next logical task based on the current build order.
```

### Rules

- Append only. Never edit or delete a previous entry.
- Keep entries short. No bloated text.
- If no decisions were made during the task, write "None".
- One entry per task. Not per file, not per session.
- Never log secrets, API keys, or tokens.

---

## 8. QUICK CHECKLIST

Before responding to any task, confirm:

- [ ] I have read this file in full this session
- [ ] I have read all docs in `/docs` in the correct order
- [ ] I have checked `BUILDLOG.md` to understand what is already built
- [ ] I have received a task brief from the user
- [ ] I have listed the files I plan to touch and waited for confirmation
- [ ] I will write tests alongside the code, not after
- [ ] I will append to `BUILDLOG.md` when the task is complete
- [ ] I will not log secrets

If any box is unchecked, fix that first.

---

**Project**: ShopKeeper AI  
**Built by**: Advait Joshi  
**Current Phase**: Phase 4 — Core Development
