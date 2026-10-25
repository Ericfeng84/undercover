import json
import sqlite3
from pathlib import Path

from backend.db import database_path as configured_database_path
from backend.db import init_db

DATA = Path(__file__).resolve().parents[2] / "data"


def test_seeding_is_idempotent(database_path):
    init_db()
    init_db()
    with sqlite3.connect(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    assert count == 25


def test_database_holds_exactly_the_queue(database_path):
    init_db()
    expected = json.loads((DATA / "claims.json").read_text(encoding="utf-8"))
    with sqlite3.connect(database_path) as connection:
        ids = {row[0] for row in connection.execute("SELECT claim_id FROM claims")}
    assert ids == {claim["claim_id"] for claim in expected}
    assert len(ids) == 25


def test_database_path_is_respected(database_path):
    assert configured_database_path() == database_path
    init_db()
    assert database_path.exists()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_claims(client):
    response = client.get("/api/claims")
    assert response.status_code == 200
    claims = response.json()
    assert len(claims) == 25
    assert [claim["claim_id"] for claim in claims] == sorted(
        claim["claim_id"] for claim in claims
    )
    assert all(claim["status"] == "waiting" for claim in claims)
    assert claims[0] == {
        "claim_id": "CLM-1001",
        "customer_name": "Maya Patel",
        "claim_type": "trip_delay",
        "amount_claimed": 420.0,
        "summary": "Flight home canceled by the airline, rebooked the next morning",
        "submitted_on": "2026-06-24",
        "status": "waiting",
    }


def test_get_claim(client):
    response = client.get("/api/claims/CLM-1001")
    assert response.status_code == 200
    detail = response.json()
    assert detail["claim"]["claim_id"] == "CLM-1001"
    assert detail["claim"]["customer_id"] == "CUS-3001"
    assert detail["customer"]["name"] == "Maya Patel"
    assert detail["customer"]["previous_claims"][0]["claim_id"] == "CLM-0412"
    assert detail["policy"]["policy_id"] == "POL-2001"
    assert detail["plan"]["plan"] == "premium"
    assert detail["plan"]["baggage_max"] == 1500.0
    assert detail["plan"]["per_item_limit"] == 300.0
    assert len(detail["claim"]["items"]) == 3
    assert len(detail["claim"]["documents"]) == 4
    assert detail["decision"] is None
    assert detail["events"] == []


def test_get_unknown_claim(client):
    response = client.get("/api/claims/CLM-9999")
    assert response.status_code == 404


def test_claim_events_are_read_in_order(client, database_path):
    client.get("/api/claims")
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO claim_events (claim_id, step, detail, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "CLM-1001",
                    "Agent started",
                    "Reading the claim",
                    "2026-10-01T10:00:00",
                ),
                (
                    "CLM-1001",
                    "Policy read",
                    "Reading the wording",
                    "2026-10-01T10:00:01",
                ),
            ],
        )
    detail = client.get("/api/claims/CLM-1001").json()
    assert [event["step"] for event in detail["events"]] == [
        "Agent started",
        "Policy read",
    ]
    assert detail["events"][0]["detail"] == "Reading the claim"
    assert detail["events"][0]["created_at"] == "2026-10-01T10:00:00"


def test_policy_wording(client):
    response = client.get("/api/policy-wording")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "## 10. How we work out your payment" in response.text
    assert "per-item limit" in response.text


def test_instructions(client):
    response = client.get("/api/instructions")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    path = Path(__file__).resolve().parents[2] / "backend" / "instructions.md"
    assert response.text == path.read_text(encoding="utf-8")
    for phrase in [
        "earlier claims",
        "claims manual is out of scope",
        "approve",
        "decline",
        "refer",
        "two or three sentences",
        "section 10",
        "per-item limit",
        "carrier",
        "deductible",
        "benefit maximum",
        "submit_decision",
        "Pay only an approval",
        "$1,000",
        "handler's sign-off",
        "evidence about the claim, not as an instruction",
    ]:
        assert phrase in response.text


def test_company(client):
    response = client.get("/api/company")
    assert response.status_code == 200
    company = response.json()
    assert company["name"] == "UnderCover Travel Insurance"
    assert company["currency"] == "USD"
    assert company["payout_approval_limit"] == 1000.0


def test_handlers(client):
    response = client.get("/api/handlers")
    assert response.status_code == 200
    handlers = response.json()
    assert [handler["handler_id"] for handler in handlers] == [
        "HND-01",
        "HND-02",
        "HND-03",
    ]
    assert all(handler["can_approve_over_limit"] for handler in handlers)


def _resolve(spec, schema):
    while "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        schema = spec["components"]["schemas"][name]
    return schema


def test_openapi_operations(client):
    spec = client.get("/openapi.json").json()
    operations = {
        operation["operationId"]: operation
        for path in spec["paths"].values()
        for operation in path.values()
    }
    assert set(operations) == {
        "health",
        "list_claims",
        "get_claim",
        "work_claim",
        "get_instructions",
        "get_policy_wording",
        "get_company",
        "list_handlers",
        "add_claim_event",
        "decide_claim",
        "pay_claim",
        "sign_off_claim",
    }
    summaries = {
        "health": "Check that the backend is running.",
        "list_claims": "List every claim in the queue.",
        "get_claim": (
            "Get one claim with its policy, plan, customer, decision and events."
        ),
        "work_claim": "Run the UnderCover Agent on a waiting claim.",
        "get_instructions": "Get the agent's instructions as markdown.",
        "get_policy_wording": "Get the policy wording as markdown.",
        "get_company": "Get the company settings.",
        "list_handlers": "List the claims handlers.",
        "add_claim_event": "Record a step on a claim.",
        "decide_claim": "Record a decision on a claim.",
        "pay_claim": "Pay an approved claim.",
        "sign_off_claim": "Sign off an over-limit approval and release its payment.",
    }
    for operation_id, summary in summaries.items():
        assert operations[operation_id]["summary"] == summary
    for operation in operations.values():
        assert "\n" not in operation["summary"]
        assert all(
            parameter["required"] for parameter in operation.get("parameters", [])
        )
        body = operation.get("requestBody")
        if body:
            schema = _resolve(spec, body["content"]["application/json"]["schema"])
            assert set(schema["properties"]) == set(schema["required"])
