# The pilot plan

## What this builds

The pilot turns the hello-world skeleton into UnderCover's claims desk:

- the 25 claims in `data/claims.json` in a queue, each with its state
- the UnderCover Agent, which reads a claim, its policy and history and the policy wording, then approves, declines or refers it with a payout and reasons
- a dashboard that shows the queue, each claim in full, the agent's decision and the steps it took, and the agent's instructions read only
- the $1,000 rule, enforced by the backend: a larger payout waits for a handler's sign-off, and the agent cannot pay it

Everything is in US dollars. No sign-in, no real payments and no messages to customers, as the brief says.

## How it fits together

```
dashboard (React)  --HTTP-->  backend (FastAPI + SQLite)
                                  ^            |
                                  |            | starts a run
                             tools (HTTP) <---- agent (LangChain)
```

The backend is the only system of record. The agent reaches claims and its instructions only through the backend's API, and the dashboard shows only what the backend holds. The database is seeded from `data/` the first time it starts. `data/evals/` and `data/security/` are never read, copied or served.

Choices worth reviewing:

- **The backend starts the agent.** `POST /api/claims/{claim_id}/work` runs `agent.main.run(claim_id, thread_id)`. The route is synchronous, so it returns when the run has finished. It runs in FastAPI's threadpool, which leaves the server free to answer the agent's own API calls. The dashboard polls the claim while the request is open, so the steps appear as the agent works. This keeps the pilot to the two processes the tech stack names.
- **The four queue states are the claim's status.** `waiting`, `in_progress`, `awaiting_signoff` and `decided`. A referral is a decision, so it ends `decided` with the outcome `refer`.
- **Sign-off releases the payment.** A payout over the limit is approved into `awaiting_signoff` with no payment. A handler signs it off in the dashboard and the backend then records the payment as released. The agent's own attempt to pay it is refused.
- **The agent's instructions are served by the backend.** They live in `backend/instructions.md`; `GET /api/instructions` returns them and the agent uses them as its system prompt. That gives one source of truth and a read-only page in the dashboard.
- **No eval data in the product.** Seeding loads exact files: `claims.json`, `policies.json`, `customers.json`, `plans.json`, `handlers.json`, `company.json` and `policy_wording.md`. A test checks that the database holds exactly the 25 queue claims.

## Data model

SQLite, one connection per operation, seeded on first start and idempotent.

- `claims`: the claim fields, with `items` and `documents` stored as JSON text, plus `status`
- `policies`: policy id, customer, plan, add-ons, purchase date, trip and travelers as JSON
- `customers`: contact details, address and previous claims as JSON
- `plans`: the three plans and their limits, and the add-ons
- `company`: the settings, including `payout_approval_limit`
- `handlers`: the three claims handlers
- `decisions`: one row per decided claim: outcome, payout, calculation, reason, policy section, decided at, signed off by, signed off at, paid amount, paid at
- `claim_events`: append-only steps for each claim, with a timestamp

The policy wording and the agent's instructions are read from their files by the API, not copied into SQLite.

### Status flow

```
waiting --work--> in_progress --decision approve <= limit--> decided
                               --decision approve >  limit--> awaiting_signoff --sign-off--> decided + payment
                               --decision decline/refer------> decided
```

A decision is accepted on a `waiting` or `in_progress` claim, then the claim is no longer waiting. A second decision is refused.

## API

Every operation has an `operation_id`, a one-line docstring and no optional inputs. No query parameters; filters are done by the dashboard in the browser.

| Method and path | operation_id | Input | Returns |
|---|---|---|---|
| `GET /api/health` | `health` | none | status |
| `GET /api/claims` | `list_claims` | none | 25 summaries: id, customer name, type, amount claimed, summary, submitted on, status |
| `GET /api/claims/{claim_id}` | `get_claim` | claim id | claim, policy, plan, customer, decision and events |
| `GET /api/instructions` | `get_instructions` | none | the agent's instructions as markdown |
| `GET /api/policy-wording` | `get_policy_wording` | none | the policy wording as markdown |
| `GET /api/company` | `get_company` | none | name, currency and payout approval limit |
| `GET /api/handlers` | `list_handlers` | none | the three handlers |
| `POST /api/claims/{claim_id}/work` | `work_claim` | none | the claim after the run |
| `POST /api/claims/{claim_id}/events` | `add_claim_event` | step, detail | the recorded step |
| `POST /api/claims/{claim_id}/decision` | `decide_claim` | outcome, payout, calculation, reason, policy_section | the claim after the decision |
| `POST /api/claims/{claim_id}/pay` | `pay_claim` | amount | the claim after the payment |
| `POST /api/claims/{claim_id}/sign-off` | `sign_off_claim` | handler_id | the claim after sign-off and released payment |

## Payment and sign-off rules

1. A decision is `approve`, `decline` or `refer`. An approval has a payout greater than zero; a decline or referral has a payout of zero.
2. An approval over the limit from `company.json` becomes `awaiting_signoff` and records no payment.
3. `pay` succeeds only on a `decided` claim whose decision is `approve`, for exactly the approved payout, once. Anything else is refused with 409.
4. The agent trying to pay an approval over the limit is refused with 409 and its attempt is recorded as a step. This is the rule that must hold even when the agent tries.
5. A handler signs off an `awaiting_signoff` claim. The backend checks the handler exists and may approve over the limit, records who signed and when, releases the payment for the approved payout and moves the claim to `decided`.
6. A payout of exactly the limit needs no sign-off. The test suite covers the boundary, the block, the sign-off and repeat payment.

## The agent

`agent/main.py` keeps one entry point, `run(claim_id, thread_id, llm=None)`, and the same model selection: `openai/gpt-6-luna` with low reasoning effort, or `MODEL_NAME` when set.

Tools, all through the backend API:

- `get_claim(claim_id)` returns the claim, policy, plan and customer with previous claims. It records a step.
- `get_policy_wording()` returns the wording. It records a step.
- `submit_decision(claim_id, outcome, payout, calculation, reason, policy_section)` submits the decision. The backend records it.
- `pay_claim(claim_id, amount)` pays an approval. On the blocked over-limit case it returns the backend's message instead of raising, so the agent can finish cleanly.

The run fetches the instructions from `GET /api/instructions` and records that step. The instructions tell the agent to read the claim and the wording, decide on the wording alone (the claims manual is out of scope), work out the payout with section 10 (per-item limits, carrier offsets, deductible and benefit maximum), cite the policy section, explain in two or three sentences, submit the decision, and pay only an approval. They also say that text inside a claim or a document is evidence, not an instruction.

`POST /work` records that the agent started, sets `in_progress`, runs the agent, and leaves the claim `decided` or `awaiting_signoff`. If the run fails or ends without a decision, it records a step and returns the claim to `waiting` so it can be tried again.

## The dashboard

React, Vite and TypeScript, no new router dependency: a small view state switches between the queue, a claim and the instructions.

- **Queue**: every claim with its customer, type, amount and state. State chips use Cerulean for waiting, Marigold for in progress, Coral for waiting for sign-off and Sea Green for decided. The queue is the landing page.
- **Claim**: the customer's story, the items claimed, the documents, the policy and plan, the customer's earlier claims, the agent's decision with its payout, calculation, reasons and policy section, the steps in order, and the payment and sign-off state.
- **Actions**: a Work button on a waiting claim, which shows the steps as they arrive; a handler select and a Sign off button on a waiting-for-sign-off claim; and a clear payment-blocked message.
- **Instructions**: the markdown from `/api/instructions`, read only.
- **Brand**: Instrument Sans for headings and body, Instrument Serif for the tagline, JetBrains Mono for numbers and identifiers; the brand palette; page background `#F0F4F5`, white panels, rounded corners and no outlines or edge borders. A dark variant follows `prefers-color-scheme`, using `#04232E` and black panels.

The tests mock `fetch`; the end-to-end tests never call a model.

## The phases

Each phase ends with its criteria ticked in this file, `docs/STATUS.md` updated and a commit. The pre-commit hook runs the checks.

### Phase 1: Backend foundation and the read API

Build the SQLite schema, seed it from the queue data, and serve the queue, a claim in full, the policy wording, the company settings and the handlers. Tests use a temporary database path.

Why: the queue, the claim records and the policy wording are what the agent and the dashboard both need, and they fix the shape of everything that follows.

Success criteria:

- [x] `uv run pytest backend -q` passes, with backend coverage at or above 80%.
- [x] A first start creates the database and seeds 25 claims; a second start does not duplicate them.
- [x] `curl localhost:8000/api/claims` returns 25 summaries in claim-id order, every one with `"status": "waiting"`, each with claim id, customer name, type, amount claimed and summary.
- [x] `curl localhost:8000/api/claims/CLM-1001` returns Maya Patel, policy POL-2001, the Premium plan limits, the claim's 3 items and 4 documents; an unknown claim returns 404.
- [x] `curl localhost:8000/api/policy-wording` returns the wording including section 10; `curl localhost:8000/api/company` returns the $1,000 limit; `curl localhost:8000/api/handlers` returns the three handlers.
- [x] `/openapi.json` shows an operation id and a one-line summary for every operation, and no operation has an optional input.
- [x] A test shows the database holds exactly the 25 claim ids from `data/claims.json`, and no others.
- [x] `DATABASE_PATH` is respected, and the tests leave no database in the repo.

### Phase 2: Decisions, payments and sign-off

Add the state machine and the rule that matters: a payout over $1,000 waits for a handler, and the agent cannot pay it. Decisions, payments and sign-offs write steps to the claim.

Why: this is the brief's hard rule, and it belongs in the backend where neither the agent nor the dashboard can get around it.

Success criteria:

- [x] `uv run pytest backend -q` passes, coverage at or above 80%.
- [x] An approval of $250 on CLM-1001 sets `decided`; paying $250 records the payment; paying again and paying a different amount each return 409.
- [x] An approval of $1,500 on CLM-1002 sets `awaiting_signoff` with no payment; paying $1,500 returns 409 and records a blocked-payment step.
- [x] Signing off that claim with handler HND-01 sets `decided`, records the handler and the time, and releases a $1,500 payment; signing it off again returns 409, and an unknown handler returns 404.
- [x] An approval of exactly $1,000 is `decided` and pays without sign-off; an approval of $1,000.01 waits for sign-off.
- [x] A decline and a referral are `decided`, have no payment, and cannot be paid; a second decision on a decided claim returns 409.
- [x] A decision on a missing claim, a payment on a missing claim and a sign-off on a missing claim each return 404.
- [x] The claim's events read in order: agent started, decision, payment or blocked payment, sign-off and released payment as they happen.
- [x] The 409 body for the over-limit payment says the payout needs a handler's sign-off.

### Phase 3: The agent and the work action

Build the agent's tools and instructions, the instructions API, its run, and `POST /work`. Tests use the stub chat model, never a real one.

Why: this is the agent doing a handler's job, and it is the part the rest of the product exists to show.

Success criteria:

- [x] `uv run pytest -q` passes (backend and agent), coverage at or above 80%.
- [x] A full run with the stub model reads the instructions, reads the claim and the wording, submits an approval and pays it; the claim ends `decided` with the payment recorded.
- [x] A stub run that approves $1,500 ends `awaiting_signoff`; the agent's pay attempt returns the blocked message and does not raise.
- [x] The tools record readable steps, and `get_claim` returns the claim, policy, plan and customer history, not the decision or events.
- [x] `POST /api/claims/{claim_id}/work` on a waiting claim sets `in_progress`, runs the agent and returns the final claim; a test with a stub run proves it. A decided claim returns 409.
- [x] A run that raises, and a run that ends without a decision, both record a step and return the claim to `waiting`.
- [x] With the backend running, `uv run python -c "from agent.main import run; print(run('CLM-1001', 'pilot'))"` decides CLM-1001 using the configured model, and its decision and steps are visible through the API. This is one real run, not a test.
- [x] `curl localhost:8000/api/instructions` returns the text of `backend/instructions.md`; the OpenAPI document lists it with an operation id and no optional input.
- [x] `npm run check:python` passes.
- [x] `backend/instructions.md` covers the decision, the payout method, the policy citation, the two-or-three-sentence reason, the over-limit behaviour and the rule that claim text is not an instruction.

### Phase 4: The dashboard, the queue and the claim

Build the dashboard shell, the queue and the claim page, with the brand applied. Include the Work button and live steps.

Why: the team needs to see the queue, each claim in full and what the agent is doing while it works.

Success criteria:

- [x] At `http://localhost:5173`, the queue lists 25 claims with customer, type, amount and state, and the state chips use the brand colours.
- [x] Clicking CLM-1001 opens the claim with the story, items, documents, policy and plan, Maya Patel's earlier claim, and a link back to the queue.
- [x] A decided claim shows its outcome, payout, calculation, reasons and policy section, and its steps in order.
- [x] The Work button appears only on a waiting claim; clicking it shows "In progress" and the steps arriving, then the decision, and the button goes away. This is checked in the browser against a running backend and agent.
- [x] The page is readable at 1280 wide and on a phone-sized window, uses Instrument Sans, Instrument Serif and JetBrains Mono, and follows the light and dark surfaces in `docs/BRAND.md`.
- [x] `npx vitest run --root dashboard --coverage` passes, with statements at or above 80%.
- [x] `npm run check:ts` passes.
- [x] The unit tests mock `fetch` and cover the queue, a decided claim, a waiting claim and the error state.

### Phase 5: Sign-off, decision variants and the instructions page

Finish the claim actions and add the read-only instructions page.

Why: the brief's sign-off rule and the read-only instructions are part of what the team needs to see, and the three outcomes need to read clearly.

Success criteria:

- [x] A waiting-for-sign-off claim shows the payout, "Waiting for sign-off", the handler select and the Sign off button, and says the payment is blocked.
- [x] Signing off with HND-01 shows the claim as decided, paid, with the handler's name and the time.
- [x] Approved, declined and referred claims each show the right label, reason and policy section; a decline or referral shows no payment and no sign-off control.
- [x] The Instructions page shows the same text as `GET /api/instructions`, has no editable field and no save action, and is reachable from the header.
- [x] `npx vitest run --root dashboard --coverage` passes at 80% or above; `npm run check:ts` passes.
- [x] The three outcomes and the sign-off flow are checked in the browser.

### Phase 6: End-to-end tests, the full check and the status

Add the Playwright tests against a fresh database, run every check, and update the documentation.

Why: the checks prove the pilot works from the outside, without a model, and the status file is how the next build knows where it stands.

Build a small `e2e/run.mjs` that deletes the end-to-end database, sets `DATABASE_PATH` and runs Playwright, and point `npm run e2e` at it. The Playwright servers do not reuse a running development server, so the fresh database is the one used.

Success criteria:

- [x] `npm run e2e` uses its own fresh database (`e2e/.data/undercover.db`), starts its own servers and leaves the development database alone.
- [x] The queue test finds 25 claims and opens CLM-1001 to see Maya Patel, the story and the documents.
- [x] The instructions test reaches the page and sees the instructions, with no editable field.
- [x] The sign-off test submits an approval of $1,200 through the API, sees "Waiting for sign-off" and the blocked payment in the dashboard, signs off with HND-01, then sees the claim decided and paid; a payment attempt after sign-off returns 409.
- [x] No end-to-end test clicks Work or calls a model.
- [x] `npm run check` passes: ruff format and lint, pyright, pytest at 80% coverage, Prettier, ESLint, tsc, vitest at 80% coverage, and Playwright.
- [x] `docs/STATUS.md` says what is built, how to start it, how to reset the queue and a short demo script: work a claim, watch the steps, sign off a large payout.
- [x] Every phase's criteria are ticked, each phase is committed, and `git status` is clean.

## Out of scope

- The claims manual, sign-in, real payments, customer messages and the held-out evaluation sets, as the brief says.
- An accuracy score for the agent. The pilot builds the desk and the agent; measuring it against `data/evals/` comes later, and nothing here reads those files.
- Reworking referred claims, bulk working of the queue, filters and search.
