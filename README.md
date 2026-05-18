# ShopKeeper AI

> 🚧 **Status: In Development** - Design & architecture complete. Build phase starting soon.

ShopKeeper AI is a retro pixel-art game backed by a real multi-agent AI system. Eight agents handle sales, inventory, payments, and fulfillment autonomously. You can play as the customer, switch to the businessman mid-session, and watch every agent decision traced live on the dashboard.

---

## The Concept

Most agentic AI demos are either a boring chat window or an over-engineered diagram nobody reads. ShopKeeper AI makes the system tangible — you can experience it from both sides of the same transaction.

**As the customer**: you wake up at home, open an in-game phone, chat with the Sales Agent, walk to the store, and checkout. Every agent fires in the background.

**As the businessman**: you stand behind the counter watching in-person NPCs and an online order feed simultaneously. A live dashboard shows what every agent is doing, why it made a decision, and how long it took.

**Switch at any time.**: The character you leave behind keeps running autonomously via AI.

---

## Agent Roster

| Agent | Type | Responsibility |
|---|---|---|
| Sales Agent | LLM - Supervisor | Orchestrates the full conversation. Routes to worker agents. Maintains customer state. |
| Recommendation Agent | LLM | Personalised product suggestions based on intent, taste, occasion, and budget. |
| Inventory Agent | Deterministic | Real-time stock check, reserve stock logic, out-of-stock signals. |
| Payment Agent | Deterministic | Simulated UPI state machine with retry logic and balance deduction. |
| Fulfillment Agent | Deterministic | Delivery scheduling and in-store pickup slot booking. |
| Loyalty & Offers Agent | Deterministic | Apply coupons, compute and issue loyalty points, promo codes. |
| Supplier Agent | LLM | Monitors sales patterns and demand signals. Recommends restocking. |
| Post-Purchase Agent | LLM | Handles returns, complaints, tracking queries, and feedback. |

All agents communicate through structured state only, no natural language between agents.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| API | FastAPI + WebSockets |
| Database | Supabase Postgres + SQLAlchemy + Alembic |
| Auth | bcrypt + python-jose + Google OAuth |
| Cache | Upstash Redis |
| Observability | LangSmith + OpenTelemetry |
| Guardrails | Pydantic strict schemas + output parser |
| Frontend | React + Tailwind CSS + Phaser 3 |
| LLM | Groq |
| Deployment | Render (backend) + Vercel (frontend) |

---

## Key Design Decisions

- **State over message history**: agents receive a compact structured state object, not full conversation history. Context windows stay small.
- **LLMs only where reasoning is needed**: Sales, Recommendation, Supplier, Post-Purchase, and Customer Generator use LLMs. Everything else is a deterministic function call.
- **Observability as a game mechanic**: the businessman dashboard is the observability layer. Agent traces surface inside the UI, not in a separate tool.
- **Guardrails are non-negotiable**: all agent inputs and outputs are validated through Pydantic strict schemas.

---

## Project Phases

- [x] Phase 1 - Discovery & Planning (PRD complete)
- [x] Phase 2 - Design & Architecture (API contract + DB schema complete)
- [ ] Phase 3 - Build
- [ ] Phase 4 - Deployment & Observability

---

*Built by [Advait Joshi](https://www.linkedin.com/in/advaitszone/)*