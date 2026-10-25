import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent import main
from backend.main import app


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture
def client(monkeypatch):
    with TestClient(app) as test_client:
        monkeypatch.setattr(main, "backend", lambda: TestClient(app))
        yield test_client


def tool_call(name, args, call_id):
    return AIMessage(
        content="", tool_calls=[{"name": name, "args": args, "id": call_id}]
    )


def decision_args(claim_id, outcome, payout):
    return {
        "claim_id": claim_id,
        "outcome": outcome,
        "payout": payout,
        "calculation": "Eligible costs less the deductible.",
        "reason": "The policy wording covers the claim.",
        "policy_section": "Section 10",
    }


def test_full_run_approves_and_pays(client):
    replies = [
        tool_call("get_claim", {"claim_id": "CLM-1001"}, "1"),
        tool_call("get_policy_wording", {}, "2"),
        tool_call("submit_decision", decision_args("CLM-1001", "approve", 250), "3"),
        tool_call("pay_claim", {"claim_id": "CLM-1001", "amount": 250}, "4"),
        AIMessage(content="Approved and paid."),
    ]

    assert (
        main.run("CLM-1001", "thread-1", StubModel(messages=iter(replies)))
        == "Approved and paid."
    )

    detail = client.get("/api/claims/CLM-1001").json()
    assert detail["claim"]["status"] == "decided"
    assert detail["decision"]["outcome"] == "approve"
    assert detail["decision"]["payout"] == 250.0
    assert detail["decision"]["paid_amount"] == 250.0
    assert [event["step"] for event in detail["events"]] == [
        "Read instructions",
        "Read claim",
        "Read policy wording",
        "Decision",
        "Payment",
    ]
    assert detail["events"][1]["detail"] == (
        "Read CLM-1001 for Maya Patel: trip delay, $420.00 claimed."
    )


def test_full_run_with_an_over_limit_approval(client):
    replies = [
        tool_call("get_claim", {"claim_id": "CLM-1002"}, "1"),
        tool_call("get_policy_wording", {}, "2"),
        tool_call("submit_decision", decision_args("CLM-1002", "approve", 1500), "3"),
        tool_call("pay_claim", {"claim_id": "CLM-1002", "amount": 1500}, "4"),
        AIMessage(content="The payout needs a handler's sign-off."),
    ]

    result = main.run("CLM-1002", "thread-2", StubModel(messages=iter(replies)))
    assert result == "The payout needs a handler's sign-off."

    detail = client.get("/api/claims/CLM-1002").json()
    assert detail["claim"]["status"] == "awaiting_signoff"
    assert detail["decision"]["payout"] == 1500.0
    assert detail["decision"]["paid_amount"] is None
    assert detail["events"][-1]["step"] == "Payment blocked"


def test_pay_tool_returns_the_blocked_message(client):
    main.submit_decision.invoke(decision_args("CLM-1002", "approve", 1500))
    message = main.pay_claim.invoke({"claim_id": "CLM-1002", "amount": 1500})
    assert message == "Payout needs a handler's sign-off."


def test_get_claim_tool_returns_the_claim_without_decision_or_events(client):
    result = main.get_claim.invoke({"claim_id": "CLM-1001"})
    assert set(result) == {"claim", "policy", "plan", "customer"}
    assert result["claim"]["claim_id"] == "CLM-1001"
    assert result["customer"]["name"] == "Maya Patel"
    assert result["customer"]["previous_claims"][0]["claim_id"] == "CLM-0412"
    assert result["plan"]["plan"] == "premium"
    assert "decision" not in result
    assert "events" not in result

    events = client.get("/api/claims/CLM-1001").json()["events"]
    assert events[-1]["step"] == "Read claim"
    assert "Maya Patel" in events[-1]["detail"]


def test_policy_wording_tool_records_a_step(client):
    token = main.current_claim.set("CLM-1001")
    try:
        wording = main.get_policy_wording.invoke({})
    finally:
        main.current_claim.reset(token)

    assert "## 10. How we work out your payment" in wording
    events = client.get("/api/claims/CLM-1001").json()["events"]
    assert events[-1]["step"] == "Read policy wording"


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
