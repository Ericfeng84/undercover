"""Queries for the claims desk."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException

from backend import db
from backend.models import DecisionRequest, EventRequest, PayRequest, SignOffRequest

OUTCOME_LABELS = {
    "approve": "Approved",
    "decline": "Declined",
    "refer": "Referred",
}


def list_claims() -> list[dict[str, Any]]:
    """Return every claim summary in claim-id order."""
    with db.connect() as connection:
        rows = connection.execute(
            """
            SELECT
                claims.claim_id, customers.name AS customer_name,
                claims.claim_type, claims.amount_claimed, claims.summary,
                claims.submitted_on, claims.status
            FROM claims
            JOIN customers ON customers.customer_id = claims.customer_id
            ORDER BY claims.claim_id
            """
        ).fetchall()
    return [
        {
            "claim_id": row["claim_id"],
            "customer_name": row["customer_name"],
            "claim_type": row["claim_type"],
            "amount_claimed": row["amount_claimed"],
            "summary": row["summary"],
            "submitted_on": row["submitted_on"],
            "status": row["status"],
        }
        for row in rows
    ]


def get_claim(claim_id: str) -> dict[str, Any]:
    """Return a claim with its policy, plan, customer, decision and events."""
    with db.connect() as connection:
        return claim_detail(connection, claim_id)


def claim_detail(connection: Any, claim_id: str) -> dict[str, Any]:
    """Build the full claim record from one connection."""
    claim = require_claim(connection, claim_id)
    policy = connection.execute(
        "SELECT * FROM policies WHERE policy_id = ?", (claim["policy_id"],)
    ).fetchone()
    customer = connection.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (claim["customer_id"],)
    ).fetchone()
    plans = json.loads(
        connection.execute("SELECT data FROM plans WHERE id = 1").fetchone()["data"]
    )
    plan = next(item for item in plans["plans"] if item["plan"] == policy["plan"])
    decision = connection.execute(
        "SELECT * FROM decisions WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    events = connection.execute(
        "SELECT * FROM claim_events WHERE claim_id = ? ORDER BY id", (claim_id,)
    ).fetchall()
    return {
        "claim": claim_record(claim),
        "policy": policy_record(policy),
        "plan": plan,
        "customer": customer_record(customer),
        "decision": decision_record(decision),
        "events": [event_record(event) for event in events],
    }


def require_claim(connection: Any, claim_id: str) -> Any:
    """Return the claim row, or 404."""
    claim = connection.execute(
        "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


def claim_record(row: Any) -> dict[str, Any]:
    """Return a claim row as an API record."""
    return {
        "claim_id": row["claim_id"],
        "policy_id": row["policy_id"],
        "customer_id": row["customer_id"],
        "claim_type": row["claim_type"],
        "submitted_on": row["submitted_on"],
        "incident_date": row["incident_date"],
        "incident_location": row["incident_location"],
        "summary": row["summary"],
        "story": row["story"],
        "items": json.loads(row["items"]),
        "amount_claimed": row["amount_claimed"],
        "documents": json.loads(row["documents"]),
        "status": row["status"],
    }


def policy_record(row: Any) -> dict[str, Any]:
    """Return a policy row as an API record."""
    return {
        "policy_id": row["policy_id"],
        "customer_id": row["customer_id"],
        "plan": row["plan"],
        "add_ons": json.loads(row["add_ons"]),
        "purchased_on": row["purchased_on"],
        "sold_through": row["sold_through"],
        "trip": json.loads(row["trip"]),
        "travelers": json.loads(row["travelers"]),
        "status": row["status"],
    }


def customer_record(row: Any) -> dict[str, Any]:
    """Return a customer row as an API record."""
    return {
        "customer_id": row["customer_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "date_of_birth": row["date_of_birth"],
        "address": json.loads(row["address"]),
        "customer_since": row["customer_since"],
        "previous_claims": json.loads(row["previous_claims"]),
    }


def decision_record(row: Any) -> dict[str, Any] | None:
    """Return a decision row as an API record, or None."""
    if row is None:
        return None
    return {
        "outcome": row["outcome"],
        "payout": row["payout_cents"] / 100,
        "calculation": row["calculation"],
        "reason": row["reason"],
        "policy_section": row["policy_section"],
        "decided_at": row["decided_at"],
        "signed_off_by": row["signed_off_by"],
        "signed_off_at": row["signed_off_at"],
        "paid_amount": (
            None if row["paid_amount_cents"] is None else row["paid_amount_cents"] / 100
        ),
        "paid_at": row["paid_at"],
    }


def event_record(row: Any) -> dict[str, Any]:
    """Return a claim event row as an API record."""
    return {
        "id": row["id"],
        "claim_id": row["claim_id"],
        "step": row["step"],
        "detail": row["detail"],
        "created_at": row["created_at"],
    }


def get_company() -> dict[str, Any]:
    """Return the company settings."""
    with db.connect() as connection:
        return json.loads(
            connection.execute("SELECT data FROM company WHERE id = 1").fetchone()[
                "data"
            ]
        )


def list_handlers() -> list[dict[str, Any]]:
    """Return the claims handlers."""
    with db.connect() as connection:
        rows = connection.execute(
            "SELECT * FROM handlers ORDER BY handler_id"
        ).fetchall()
    return [
        {
            "handler_id": row["handler_id"],
            "name": row["name"],
            "role": row["role"],
            "email": row["email"],
            "can_approve_over_limit": bool(row["can_approve_over_limit"]),
        }
        for row in rows
    ]


def policy_wording() -> str:
    """Return the policy wording markdown."""
    return (db.DATA_DIR / "policy_wording.md").read_text(encoding="utf-8")


def now() -> str:
    """Return the current time as an ISO timestamp."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def to_cents(amount: Decimal) -> int:
    """Turn an amount in dollars into whole cents."""
    return int(amount * 100)


def money_text(cents: int) -> str:
    """Format whole cents as dollars."""
    return f"${cents / 100:,.2f}"


def company_settings(connection: Any) -> dict[str, Any]:
    """Return the company settings from the database."""
    row = connection.execute("SELECT data FROM company WHERE id = 1").fetchone()
    return json.loads(row["data"])


def payout_limit_cents(connection: Any) -> int:
    """Return the payout approval limit in cents."""
    limit = company_settings(connection)["payout_approval_limit"]
    return to_cents(Decimal(str(limit)))


def record_event(
    connection: Any, claim_id: str, step: str, detail: str
) -> dict[str, Any]:
    """Append a step to a claim and return it."""
    created_at = now()
    cursor = connection.execute(
        """
        INSERT INTO claim_events (claim_id, step, detail, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (claim_id, step, detail, created_at),
    )
    return {
        "id": cursor.lastrowid,
        "claim_id": claim_id,
        "step": step,
        "detail": detail,
        "created_at": created_at,
    }


def add_claim_event(claim_id: str, request: EventRequest) -> dict[str, Any]:
    """Record a step on a claim."""
    with db.connect() as connection:
        require_claim(connection, claim_id)
        return record_event(connection, claim_id, request.step, request.detail)


def decide_claim(claim_id: str, request: DecisionRequest) -> dict[str, Any]:
    """Record a decision on a claim."""
    with db.connect() as connection:
        claim = require_claim(connection, claim_id)
        if claim["status"] not in {"waiting", "in_progress"}:
            raise HTTPException(
                status_code=409, detail="Claim has already been decided"
            )
        payout = to_cents(request.payout)
        if request.outcome == "approve" and payout == 0:
            raise HTTPException(status_code=422, detail="An approval needs a payout")
        if request.outcome != "approve" and payout != 0:
            raise HTTPException(
                status_code=422, detail="A decline or referral pays nothing"
            )
        status = "decided"
        if request.outcome == "approve" and payout > payout_limit_cents(connection):
            status = "awaiting_signoff"
        connection.execute(
            """
            INSERT INTO decisions (
                claim_id, outcome, payout_cents, calculation, reason,
                policy_section, decided_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                request.outcome,
                payout,
                request.calculation,
                request.reason,
                request.policy_section,
                now(),
            ),
        )
        connection.execute(
            "UPDATE claims SET status = ? WHERE claim_id = ?", (status, claim_id)
        )
        record_event(
            connection,
            claim_id,
            "Decision",
            f"{OUTCOME_LABELS[request.outcome]} {money_text(payout)}. {request.reason}",
        )
        return claim_detail(connection, claim_id)


def pay_claim(claim_id: str, request: PayRequest) -> dict[str, Any]:
    """Pay an approved claim."""
    with db.connect() as connection:
        claim = require_claim(connection, claim_id)
        decision = require_decision(connection, claim_id)
        amount = to_cents(request.amount)
        if claim["status"] == "awaiting_signoff":
            record_event(
                connection,
                claim_id,
                "Payment blocked",
                "Payout needs a handler's sign-off.",
            )
            connection.commit()
            raise HTTPException(
                status_code=409, detail="Payout needs a handler's sign-off."
            )
        if claim["status"] != "decided" or decision["outcome"] != "approve":
            raise HTTPException(
                status_code=409, detail="Only an approved claim can be paid"
            )
        if decision["paid_amount_cents"] is not None:
            raise HTTPException(status_code=409, detail="Claim has already been paid")
        if amount != decision["payout_cents"]:
            raise HTTPException(
                status_code=409, detail="Amount does not match the approved payout"
            )
        paid_at = now()
        connection.execute(
            """
            UPDATE decisions SET paid_amount_cents = ?, paid_at = ?
            WHERE claim_id = ?
            """,
            (amount, paid_at, claim_id),
        )
        record_event(
            connection,
            claim_id,
            "Payment",
            f"Paid {money_text(amount)}.",
        )
        return claim_detail(connection, claim_id)


def require_decision(connection: Any, claim_id: str) -> Any:
    """Return the claim's decision, or 409."""
    decision = connection.execute(
        "SELECT * FROM decisions WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    if decision is None:
        raise HTTPException(status_code=409, detail="Claim has no decision")
    return decision


def sign_off_claim(claim_id: str, request: SignOffRequest) -> dict[str, Any]:
    """Sign off an over-limit approval and release its payment."""
    with db.connect() as connection:
        claim = require_claim(connection, claim_id)
        handler = connection.execute(
            "SELECT * FROM handlers WHERE handler_id = ?", (request.handler_id,)
        ).fetchone()
        if handler is None:
            raise HTTPException(status_code=404, detail="Handler not found")
        if claim["status"] != "awaiting_signoff":
            raise HTTPException(
                status_code=409, detail="Claim is not waiting for sign-off"
            )
        if not handler["can_approve_over_limit"]:
            raise HTTPException(
                status_code=409, detail="This handler cannot approve over the limit"
            )
        decision = require_decision(connection, claim_id)
        signed_at = now()
        connection.execute(
            """
            UPDATE decisions
            SET signed_off_by = ?, signed_off_at = ?,
                paid_amount_cents = ?, paid_at = ?
            WHERE claim_id = ?
            """,
            (
                request.handler_id,
                signed_at,
                decision["payout_cents"],
                signed_at,
                claim_id,
            ),
        )
        connection.execute(
            "UPDATE claims SET status = 'decided' WHERE claim_id = ?", (claim_id,)
        )
        record_event(
            connection,
            claim_id,
            "Sign-off",
            f"Signed off by {handler['name']}.",
        )
        record_event(
            connection,
            claim_id,
            "Payment released",
            f"Paid {money_text(decision['payout_cents'])}.",
        )
        return claim_detail(connection, claim_id)
