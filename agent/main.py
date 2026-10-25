"""The UnderCover Agent."""

import os
from contextvars import ContextVar
from http import HTTPStatus
from typing import Any

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://localhost:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"

current_claim: ContextVar[str] = ContextVar("current_claim")


class DecisionInput(BaseModel):
    """The fields of a decision."""

    claim_id: str
    outcome: str
    payout: float
    calculation: str
    reason: str
    policy_section: str


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=60)


def record_step(client: httpx.Client, claim_id: str, step: str, detail: str) -> None:
    """Record a readable step on the claim."""
    response = client.post(
        f"/api/claims/{claim_id}/events",
        json={"step": step, "detail": detail},
    )
    response.raise_for_status()


def fetch_instructions(claim_id: str) -> str:
    """Read the agent's instructions and record the step."""
    with backend() as client:
        response = client.get("/api/instructions")
        response.raise_for_status()
        record_step(
            client,
            claim_id,
            "Read instructions",
            "Read the UnderCover Agent instructions.",
        )
    return response.text


@tool
def get_claim(claim_id: str) -> dict[str, Any]:
    """Get a claim with its policy, plan and customer history."""
    with backend() as client:
        response = client.get(f"/api/claims/{claim_id}")
        response.raise_for_status()
        detail = response.json()
        claim = detail["claim"]
        record_step(
            client,
            claim_id,
            "Read claim",
            (
                f"Read {claim_id} for {detail['customer']['name']}: "
                f"{claim['claim_type'].replace('_', ' ')}, "
                f"${claim['amount_claimed']:,.2f} claimed."
            ),
        )
    return {
        "claim": claim,
        "policy": detail["policy"],
        "plan": detail["plan"],
        "customer": detail["customer"],
    }


@tool
def get_policy_wording() -> str:
    """Get the policy wording."""
    claim_id = current_claim.get()
    with backend() as client:
        response = client.get("/api/policy-wording")
        response.raise_for_status()
        record_step(
            client,
            claim_id,
            "Read policy wording",
            "Read the policy wording.",
        )
    return response.text


@tool(args_schema=DecisionInput)
def submit_decision(**kwargs: Any) -> dict[str, Any]:
    """Submit the decision on a claim."""
    return _submit_decision(DecisionInput(**kwargs))


def _submit_decision(decision: DecisionInput) -> dict[str, Any]:
    """Send a decision to the backend."""
    with backend() as client:
        response = client.post(
            f"/api/claims/{decision.claim_id}/decision",
            json=decision.model_dump(),
        )
        response.raise_for_status()
        detail = response.json()
    return {"status": detail["claim"]["status"], "decision": detail["decision"]}


@tool
def pay_claim(claim_id: str, amount: float) -> str:
    """Pay an approved claim for the approved payout."""
    with backend() as client:
        response = client.post(f"/api/claims/{claim_id}/pay", json={"amount": amount})
    if response.status_code == HTTPStatus.CONFLICT:
        return response.json()["detail"]
    response.raise_for_status()
    return f"Payment recorded for ${amount:,.2f}."


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Run the agent on one claim and return its final reply."""
    instructions = fetch_instructions(claim_id)
    token = current_claim.set(claim_id)
    try:
        agent = create_agent(
            llm or model(),
            tools=[get_claim, get_policy_wording, submit_decision, pay_claim],
            system_prompt=instructions,
        )
        result = agent.invoke(
            {"messages": [{"role": "user", "content": f"Work claim {claim_id}."}]},
            config={"configurable": {"thread_id": thread_id}},
        )
    finally:
        current_claim.reset(token)
    return result["messages"][-1].text
