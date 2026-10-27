# Safe Deal Link

Safe Deal Link holds a buyer's PayPal payment until AI agents verify the item
arrived as listed, then captures or voids it.

**Problem:** Peer-to-peer buyers (Facebook Marketplace, Craigslist) get
scammed. Protection today is a dispute after the loss.

**Solution:** The seller shares a deal link. The buyer pays with PayPal using
authorize intent, so money is held, not sent. Agents check the listing, the
delivery, and a photo of the received item, then release or void.

**Pitch:** Escrow exists but is manual and slow. We made it instant and
evidence-based with AI agents, using PayPal authorize and capture so no one
ever holds the money.

## Stack

| Layer | Choice |
|---|---|
| Frontend | Vue 3, Vite, Vue Router, Pinia, `@paypal/paypal-js` |
| Backend | FastAPI, SQLAlchemy, Alembic, APScheduler |
| Agents | LangGraph (Verifier → Resolver pipeline), Anthropic Claude (text + vision) |
| Database | Postgres (Docker) |
| Payments | PayPal sandbox: Orders, Authorizations, Captures, Tracking, Webhooks |
| Local tunnel | ngrok (for webhooks) |

## Architecture

### Deal lifecycle

```
CREATED → SCREENED → AUTHORIZED → SHIPPED → DELIVERED → VERIFYING → CAPTURED | VOIDED | NEEDS_HUMAN
```

Enforced in `backend/services/state.py` — only the transitions listed there
are allowed; everything else raises `InvalidTransition`.

### Agents

| Agent | Job | Guardrail |
|---|---|---|
| Listing guard | Scores scam risk before payment | Can warn, never blocks payment alone |
| Escrow agent | Watches the hold; reauthorizes or voids before expiry (scheduled) | Voids before the 29-day hard expiry |
| Verifier | Compares the buyer's photo to the listing | Read-only, never moves money |
| Resolver | Decides capture or escalate | Checked against `agents/guardrails.py` before any PayPal call |

The Resolver is the only agent allowed to move money, and every capture goes
through five guardrail checks (`agents/guardrails.py`) first: deal must be
`VERIFYING`, verifier must report a match above the 0.85 confidence
threshold, the requested amount can't exceed what was authorized, the
authorization can't be expired, and the deal can't already be captured. Any
failure sends the deal to `NEEDS_HUMAN` instead of silently proceeding.

Every agent decision is logged (`decisions` table) with its reasoning and
shown on the deal timeline; every state-changing action is logged separately
(`events` table).

### Why it fails open, not closed

Both the listing guard and verifier degrade gracefully if the LLM call
fails (missing key, network error, bad JSON) — the listing guard logs "AI
risk check unavailable" and still lets the deal proceed to payment (it can
only ever warn), while the verifier treats a failure as "no match", which
routes the deal to a human instead of either silently blocking a legitimate
sale or silently approving a bad one.

## PayPal APIs used

- `POST /v1/oauth2/token` — OAuth2 client-credentials access token
- `POST /v2/checkout/orders` — create order (`intent: AUTHORIZE`)
- `POST /v2/checkout/orders/{id}/authorize` — authorize after buyer approval
- `GET /v2/payments/authorizations/{id}` — check authorization status/expiry
- `POST /v2/payments/authorizations/{id}/capture` — capture (full or partial)
- `POST /v2/payments/authorizations/{id}/void` — void, buyer never charged
- `POST /v2/payments/authorizations/{id}/reauthorize` — renew the 3-day honor window
- `POST /v2/payments/captures/{id}/refund` — refund a completed capture
- `POST /v2/checkout/orders/{id}/track` — attach shipment tracking (post-capture only)
- `POST /v1/notifications/verify-webhook-signature` — verify inbound webhooks
- Webhooks: `PAYMENT.AUTHORIZATION.CREATED`, `PAYMENT.AUTHORIZATION.VOIDED`,
  `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.PENDING`, `PAYMENT.CAPTURE.DENIED`

Every money-moving call sends a `PayPal-Request-Id` header derived from the
deal/authorization/capture ID (not a random UUID), so a retried request is
idempotent instead of double-charging.

## Eval

`eval/run_eval.py` tests `agents/guardrails.py` — the actual capture/escalate
decision logic — against 18 synthetic cases covering honest deals, wrong
items, damaged items, unclear photos, partial delivery, and every individual
guardrail rule (amount ceiling, idempotency, expiry, wrong state). It needs
no database, PayPal credentials, or LLM key, so it's reproducible anywhere:

```
python eval/run_eval.py
```

**Result: guardrails correct on 18 of 18 (100%)** — see `eval/results.json`.

This measures whether the *code* correctly enforces safety rules given an AI
verdict, not the underlying vision model's judgment quality on real photos
(which a fixed JSON fixture can't measure honestly).

## Setup

### Phase 0 — accounts and tools

1. Create a PayPal Developer account at developer.paypal.com
2. Create a sandbox Business account (seller) and a sandbox Personal account (buyer)
3. Create a REST app; copy the Client ID and Secret
4. Get an LLM API key with vision support (this build uses Anthropic Claude)
5. Install Python 3.11+, Node 20+, Docker, and ngrok

### Environment

Copy `.env.example` to `.env` at the repo root and fill in:

| Key | Value |
|---|---|
| `PAYPAL_CLIENT_ID` / `PAYPAL_SECRET` | From the sandbox REST app |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` |
| `PAYPAL_WEBHOOK_ID` | Added after creating a webhook (Phase 5) |
| `DATABASE_URL` | `postgresql+psycopg2://safedeal:safedeal@localhost:5433/safedeal` |
| `LLM_API_KEY` | Anthropic API key |
| `VITE_PAYPAL_CLIENT_ID` | Same value as `PAYPAL_CLIENT_ID` (public, safe client-side) |

Note: Postgres is mapped to host port **5433** (not 5432) to avoid colliding
with a locally installed Postgres service — see `docker-compose.yml`.

### Run it

```
docker compose up -d                                   # Postgres

cd backend
python -m venv .venv
.venv\Scripts\activate                                  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

cd frontend
npm install
npm run dev                                              # http://localhost:5173
```

Webhooks (Phase 5): `ngrok http 8000`, then add a PayPal webhook pointing at
`https://<ngrok-url>/webhooks/paypal` subscribed to the five events listed
above, and save its ID to `PAYPAL_WEBHOOK_ID`.

Demo data: `cd backend && python -m scripts.seed_demo` creates a few deals
at different lifecycle stages (including one already in the review queue)
so the UI has something to show without a live PayPal/LLM round-trip.

## Judge Q&A

| Question | Answer |
|---|---|
| Doesn't PayPal already have buyer protection? | Protection is a dispute after the loss and doesn't cover Friends & Family payments scammers push for. This prevents the loss before money moves. |
| Hasn't escrow been done? | Yes, but manual and slow. Here AI decides from evidence, and no one holds funds because PayPal authorization keeps money in the buyer's account. |
| What if the AI is wrong? | Guardrails in code, confidence thresholds, human review for unclear cases, and a measured eval score (100% on 18 guardrail cases). |
| Why is this agentic? | Agents choose tools, act on PayPal over days, wake on a schedule, and escalate when unsure. |
| What if the buyer lies to get a void? | Out of scope for this build (see below) — today, unclear cases go to human review. |

## Out of scope

Buyer fraud against sellers (fake damage claims, return flows) — mentioned
as future work in the original build guide; not implemented here.
