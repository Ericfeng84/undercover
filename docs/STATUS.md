# Status

The pilot is built: the backend, the UnderCover Agent, the dashboard and the end-to-end tests.

## What's built

- `backend/`: FastAPI and SQLite. On first use it creates `backend/.data/undercover.db`, or the file named in `DATABASE_PATH`, and seeds the 25 queue claims, policies, customers, plans, handlers, company settings and policy wording from `data/`. It serves the health check, the claim queue, one claim in full, the policy wording, the company settings, the handlers and the agent's instructions.
- Decisions: approve, decline or refer a waiting or in-progress claim. A decision writes a step to the claim.
- Payments: an approval up to the $1,000 limit can be paid once, for the approved payout. A larger approval waits for a handler's sign-off, and the backend refuses the payment with 409 and records the blocked attempt.
- Sign-off: a handler signs off an over-limit approval, which releases the payment and moves the claim to decided.
- `agent/`: the UnderCover Agent. It reads its instructions from the backend, reads the claim and the policy wording, submits a decision, and pays an approval. Every step is recorded on the claim through the API. `POST /api/claims/{claim_id}/work` runs it on a waiting claim.
- `dashboard/`: the claims queue and a full claim page with the story, items, documents, policy and plan, customer history, decision and steps. The Work button runs the agent and polls the claim so the steps appear as they arrive. An over-limit approval shows the blocked payment and a handler select for sign-off. The instructions page shows the agent instructions read only. It follows the brand palette and the light and dark surfaces.
- `e2e/`: Playwright tests for the queue, the instructions page and the over-limit sign-off flow. `npm run e2e` runs them against a fresh database in `e2e/.data/` and leaves the development database alone.

## Install and run

```
uv sync
npm install
npm run dev
```

`npm run dev` starts the API at http://localhost:8000 and the dashboard at http://localhost:5173. `npm run check` runs every check, including the end-to-end tests.

To reset the queue, stop the backend and delete `backend/.data/undercover.db`. The next start seeds the 25 claims again.

## Demo

1. Open http://localhost:5173 and click CLM-1001.
2. Press Work this claim. The status shows In progress, the steps arrive, and the decision follows.
3. For the sign-off flow, create a $1,200 approval on CLM-1002:

```
curl -X POST localhost:8000/api/claims/CLM-1002/decision \
  -H 'content-type: application/json' \
  -d '{"outcome":"approve","payout":1200,"calculation":"Covered costs.","reason":"The loss is covered by the policy wording.","policy_section":"Sections 5 and 10"}'
```

Open CLM-1002. The page shows Waiting for sign-off and the blocked payment. Choose HND-01 and press Sign off. The claim becomes Decided and paid, with the handler and time.

4. Open Instructions from the header to read the agent's instructions.
