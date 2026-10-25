import sqlite3
from decimal import Decimal
from typing import Literal

from agent import main as agent_main
from backend import service
from backend.db import connect
from backend.models import DecisionRequest


def decision(outcome: Literal["approve", "decline", "refer"] = "approve", payout="250"):
    return DecisionRequest(
        outcome=outcome,
        payout=Decimal(payout),
        calculation="Eligible costs less the deductible.",
        reason="The policy wording covers the claim.",
        policy_section="Section 10",
    )


def test_work_runs_the_agent(client, monkeypatch):
    seen = {}

    def stub(claim_id, thread_id):
        seen["claim_id"] = claim_id
        seen["thread_id"] = thread_id
        with connect() as connection:
            seen["status"] = connection.execute(
                "SELECT status FROM claims WHERE claim_id = ?", (claim_id,)
            ).fetchone()["status"]
        service.decide_claim(claim_id, decision())
        return "done"

    monkeypatch.setattr(agent_main, "run", stub)
    response = client.post("/api/claims/CLM-1001/work")
    assert response.status_code == 200
    assert seen == {
        "claim_id": "CLM-1001",
        "thread_id": "claim-CLM-1001",
        "status": "in_progress",
    }
    detail = response.json()
    assert detail["claim"]["status"] == "decided"
    assert detail["decision"]["outcome"] == "approve"
    assert detail["decision"]["payout"] == 250.0
    assert [event["step"] for event in detail["events"]] == [
        "Agent started",
        "Decision",
    ]


def test_work_rejects_claims_that_are_not_waiting(client, database_path):
    client.post(
        "/api/claims/CLM-1001/decision",
        json={
            "outcome": "approve",
            "payout": 250,
            "calculation": "Covered",
            "reason": "Covered.",
            "policy_section": "Section 3",
        },
    )
    client.post(
        "/api/claims/CLM-1002/decision",
        json={
            "outcome": "approve",
            "payout": 1500,
            "calculation": "Covered",
            "reason": "Covered.",
            "policy_section": "Section 5",
        },
    )
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE claims SET status = 'in_progress' WHERE claim_id = 'CLM-1003'"
        )

    for claim_id in ["CLM-1001", "CLM-1002", "CLM-1003"]:
        response = client.post(f"/api/claims/{claim_id}/work")
        assert response.status_code == 409


def test_work_rejects_an_unknown_claim(client):
    assert client.post("/api/claims/CLM-9999/work").status_code == 404


def test_a_failed_run_returns_the_claim_to_waiting(client, monkeypatch):
    def fail(claim_id, thread_id):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(agent_main, "run", fail)
    response = client.post("/api/claims/CLM-1001/work")
    assert response.status_code == 200
    detail = response.json()
    assert detail["claim"]["status"] == "waiting"
    assert [event["step"] for event in detail["events"]] == [
        "Agent started",
        "Agent failed",
    ]
    assert "model unavailable" in detail["events"][-1]["detail"]


def test_a_run_without_a_decision_returns_the_claim_to_waiting(client, monkeypatch):
    monkeypatch.setattr(agent_main, "run", lambda claim_id, thread_id: "finished")
    response = client.post("/api/claims/CLM-1001/work")
    assert response.status_code == 200
    detail = response.json()
    assert detail["claim"]["status"] == "waiting"
    assert [event["step"] for event in detail["events"]] == [
        "Agent started",
        "No decision",
    ]


def test_a_failed_run_keeps_an_existing_decision(client, monkeypatch):
    def decide_then_fail(claim_id, thread_id):
        service.decide_claim(claim_id, decision())
        raise RuntimeError("lost the connection after the decision")

    monkeypatch.setattr(agent_main, "run", decide_then_fail)
    response = client.post("/api/claims/CLM-1001/work")
    assert response.status_code == 200
    detail = response.json()
    assert detail["claim"]["status"] == "decided"
    assert detail["decision"]["outcome"] == "approve"
    assert detail["events"][-1]["step"] == "Agent failed"
