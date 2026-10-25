# Status

The backend and the UnderCover Agent are built. The dashboard and the end-to-end tests are still the skeleton.

## What's built

- `backend/`: FastAPI and SQLite. On first use it creates `backend/.data/undercover.db`, or the file named in `DATABASE_PATH`, and seeds the 25 queue claims, policies, customers, plans, handlers, company settings and policy wording from `data/`. It serves the health check, the claim queue, one claim in full, the policy wording, the company settings, the handlers and the agent's instructions.
- Decisions: approve, decline or refer a waiting or in-progress claim. A decision writes a step to the claim.
- Payments: an approval up to the $1,000 limit can be paid once, for the approved payout. A larger approval waits for a handler's sign-off, and the backend refuses the payment with 409 and records the blocked attempt.
- Sign-off: a handler signs off an over-limit approval, which releases the payment and moves the claim to decided.
- `agent/`: the UnderCover Agent. It reads its instructions from the backend, reads the claim and the policy wording, submits a decision, and pays an approval. Every step is recorded on the claim through the API. `POST /api/claims/{claim_id}/work` runs it on a waiting claim.
- `dashboard/`: one page that shows whether the backend is up.
- `e2e/`: one test of that page.

## Run it

`uv sync` and `npm install` install everything. `npm run dev:backend` starts the API at http://localhost:8000, and `npm run check:python` runs the Python checks.

```
curl localhost:8000/api/claims
curl localhost:8000/api/claims/CLM-1001
curl localhost:8000/api/instructions
```

With the backend running, work a claim with the agent:

```
curl -X POST localhost:8000/api/claims/CLM-1001/work
```

The claim ends `decided` or `awaiting_signoff`, and its decision and steps are visible from `GET /api/claims/CLM-1001`. To reset the queue, stop the backend and delete `backend/.data/undercover.db`. The next start seeds it again.
