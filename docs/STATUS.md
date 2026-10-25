# Status

The backend, the UnderCover Agent and the dashboard are built. The end-to-end tests are still the skeleton and are replaced in the next phase.

## What's built

- `backend/`: FastAPI and SQLite. On first use it creates `backend/.data/undercover.db`, or the file named in `DATABASE_PATH`, and seeds the 25 queue claims, policies, customers, plans, handlers, company settings and policy wording from `data/`. It serves the health check, the claim queue, one claim in full, the policy wording, the company settings, the handlers and the agent's instructions.
- Decisions: approve, decline or refer a waiting or in-progress claim. A decision writes a step to the claim.
- Payments: an approval up to the $1,000 limit can be paid once, for the approved payout. A larger approval waits for a handler's sign-off, and the backend refuses the payment with 409 and records the blocked attempt.
- Sign-off: a handler signs off an over-limit approval, which releases the payment and moves the claim to decided.
- `agent/`: the UnderCover Agent. It reads its instructions from the backend, reads the claim and the policy wording, submits a decision, and pays an approval. Every step is recorded on the claim through the API. `POST /api/claims/{claim_id}/work` runs it on a waiting claim.
- `dashboard/`: the claims queue and a full claim page with the story, items, documents, policy and plan, customer history, decision and steps. The Work button runs the agent and polls the claim so the steps appear as they arrive. An over-limit approval shows the blocked payment and a handler select for sign-off. The instructions page shows the agent instructions read only. It follows the brand palette and the light and dark surfaces.
- `e2e/`: one old skeleton test, replaced in the next phase.

## Run it

`uv sync` and `npm install` install everything. `npm run dev` starts the API at http://localhost:8000 and the dashboard at http://localhost:5173. `npm run check:python` runs the Python checks and `npm run check:ts` runs the TypeScript checks.

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
