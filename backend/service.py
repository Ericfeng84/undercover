"""Queries for the claims desk."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from backend import db


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
