import sqlite3

from backend.db import init_db


def decide(client, claim_id, outcome="approve", payout=250.0, reason="Covered."):
    return client.post(
        f"/api/claims/{claim_id}/decision",
        json={
            "outcome": outcome,
            "payout": payout,
            "calculation": "Eligible costs less the deductible.",
            "reason": reason,
            "policy_section": "Section 10",
        },
    )


def pay(client, claim_id, amount):
    return client.post(f"/api/claims/{claim_id}/pay", json={"amount": amount})


def sign_off(client, claim_id, handler_id="HND-01"):
    return client.post(
        f"/api/claims/{claim_id}/sign-off", json={"handler_id": handler_id}
    )


def test_approval_within_limit_pays_once(client):
    response = decide(client, "CLM-1001")
    assert response.status_code == 200
    claim = response.json()
    assert claim["claim"]["status"] == "decided"
    assert claim["decision"]["outcome"] == "approve"
    assert claim["decision"]["payout"] == 250.0
    assert claim["decision"]["paid_amount"] is None

    response = pay(client, "CLM-1001", 250.0)
    assert response.status_code == 200
    claim = response.json()
    assert claim["claim"]["status"] == "decided"
    assert claim["decision"]["paid_amount"] == 250.0
    assert claim["decision"]["paid_at"] is not None
    assert [event["step"] for event in claim["events"]] == ["Decision", "Payment"]

    assert pay(client, "CLM-1001", 250.0).status_code == 409
    assert pay(client, "CLM-1001", 200.0).status_code == 409
    detail = client.get("/api/claims/CLM-1001").json()
    assert detail["decision"]["paid_amount"] == 250.0
    assert len(detail["events"]) == 2


def test_payment_must_match_the_approved_payout(client):
    decide(client, "CLM-1001")
    assert pay(client, "CLM-1001", 200.0).status_code == 409
    assert client.get("/api/claims/CLM-1001").json()["decision"]["paid_amount"] is None
    assert pay(client, "CLM-1001", 250.0).status_code == 200


def test_approval_over_limit_waits_for_signoff(client):
    claim = decide(client, "CLM-1002", payout=1500.0).json()
    assert claim["claim"]["status"] == "awaiting_signoff"
    assert claim["decision"]["payout"] == 1500.0
    assert claim["decision"]["paid_amount"] is None

    response = pay(client, "CLM-1002", 1500.0)
    assert response.status_code == 409
    assert "handler's sign-off" in response.json()["detail"]

    claim = client.get("/api/claims/CLM-1002").json()
    assert claim["decision"]["paid_amount"] is None
    assert claim["events"][-1]["step"] == "Payment blocked"
    assert "handler's sign-off" in claim["events"][-1]["detail"]


def test_sign_off_releases_the_payment(client):
    decide(client, "CLM-1002", payout=1500.0)
    pay(client, "CLM-1002", 1500.0)

    response = sign_off(client, "CLM-1002", "HND-01")
    assert response.status_code == 200
    claim = response.json()
    assert claim["claim"]["status"] == "decided"
    assert claim["decision"]["signed_off_by"] == "HND-01"
    assert claim["decision"]["signed_off_at"] is not None
    assert claim["decision"]["paid_amount"] == 1500.0
    assert claim["decision"]["paid_at"] is not None
    assert [event["step"] for event in claim["events"]] == [
        "Decision",
        "Payment blocked",
        "Sign-off",
        "Payment released",
    ]
    assert "Dana Whitfield" in claim["events"][-2]["detail"]

    assert sign_off(client, "CLM-1002", "HND-01").status_code == 409


def test_sign_off_with_an_unknown_handler(client):
    decide(client, "CLM-1002", payout=1500.0)
    response = sign_off(client, "CLM-1002", "HND-99")
    assert response.status_code == 404


def test_sign_off_on_a_claim_that_is_not_waiting(client):
    decide(client, "CLM-1001", payout=250.0)
    assert sign_off(client, "CLM-1001", "HND-01").status_code == 409


def test_sign_off_needs_a_handler_who_can_approve_over_limit(client, database_path):
    decide(client, "CLM-1002", payout=1500.0)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE handlers SET can_approve_over_limit = 0 WHERE handler_id = 'HND-02'"
        )
    assert sign_off(client, "CLM-1002", "HND-02").status_code == 409
    assert (
        client.get("/api/claims/CLM-1002").json()["claim"]["status"]
        == "awaiting_signoff"
    )


def test_payout_limit_boundary(client):
    assert decide(client, "CLM-1001", payout=1000.00).json()["claim"]["status"] == (
        "decided"
    )
    assert pay(client, "CLM-1001", 1000.00).status_code == 200

    claim = decide(client, "CLM-1002", payout=1000.01).json()
    assert claim["claim"]["status"] == "awaiting_signoff"
    assert pay(client, "CLM-1002", 1000.01).status_code == 409


def test_decline_and_refer_cannot_be_paid(client):
    declined = decide(client, "CLM-1001", outcome="decline", payout=0).json()
    assert declined["claim"]["status"] == "decided"
    assert declined["decision"]["outcome"] == "decline"
    assert declined["decision"]["payout"] == 0
    assert declined["decision"]["paid_amount"] is None
    assert pay(client, "CLM-1001", 0).status_code == 409

    referred = decide(client, "CLM-1002", outcome="refer", payout=0).json()
    assert referred["claim"]["status"] == "decided"
    assert referred["decision"]["outcome"] == "refer"
    assert pay(client, "CLM-1002", 0).status_code == 409

    assert decide(client, "CLM-1001").status_code == 409


def test_decision_validation(client):
    assert decide(client, "CLM-1001", payout=0).status_code == 422
    assert decide(client, "CLM-1001", outcome="decline", payout=10).status_code == 422
    assert decide(client, "CLM-1001", outcome="maybe").status_code == 422
    assert decide(client, "CLM-1001", payout=-10).status_code == 422
    assert decide(client, "CLM-1001", payout=10.001).status_code == 422


def test_decisions_can_be_made_on_an_in_progress_claim(client, database_path):
    init_db()
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE claims SET status = 'in_progress' WHERE claim_id = 'CLM-1001'"
        )
    response = decide(client, "CLM-1001")
    assert response.status_code == 200
    assert response.json()["claim"]["status"] == "decided"


def test_missing_claims(client):
    assert decide(client, "CLM-9999").status_code == 404
    assert pay(client, "CLM-9999", 10).status_code == 404
    assert sign_off(client, "CLM-9999").status_code == 404
    assert (
        client.post(
            "/api/claims/CLM-9999/events",
            json={"step": "Agent started", "detail": "Reading the claim"},
        ).status_code
        == 404
    )


def test_pay_and_sign_off_need_a_decision(client):
    assert pay(client, "CLM-1001", 10).status_code == 409
    assert sign_off(client, "CLM-1001").status_code == 409


def test_events_are_recorded_in_order(client):
    response = client.post(
        "/api/claims/CLM-1002/events",
        json={"step": "Agent started", "detail": "Reading the claim"},
    )
    assert response.status_code == 200
    event = response.json()
    assert event["step"] == "Agent started"
    assert event["detail"] == "Reading the claim"
    assert event["created_at"]

    decide(client, "CLM-1002", payout=1500.0)
    pay(client, "CLM-1002", 1500.0)
    sign_off(client, "CLM-1002", "HND-01")

    events = client.get("/api/claims/CLM-1002").json()["events"]
    assert [event["step"] for event in events] == [
        "Agent started",
        "Decision",
        "Payment blocked",
        "Sign-off",
        "Payment released",
    ]
    assert [event["id"] for event in events] == sorted(event["id"] for event in events)
