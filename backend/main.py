"""The UnderCover backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute

from backend import service
from backend.db import init_db


class SummaryRoute(APIRoute):
    """Use the endpoint's docstring line as the OpenAPI summary."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.summary is None and self.description:
            self.summary = self.description.splitlines()[0]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create and seed the database before serving."""
    init_db()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)
app.router.route_class = SummaryRoute


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims() -> list[dict[str, Any]]:
    """List every claim in the queue."""
    return service.list_claims()


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str) -> dict[str, Any]:
    """Get one claim with its policy, plan, customer, decision and events."""
    return service.get_claim(claim_id)


@app.get(
    "/api/policy-wording",
    operation_id="get_policy_wording",
    response_class=PlainTextResponse,
)
def get_policy_wording() -> PlainTextResponse:
    """Get the policy wording as markdown."""
    return PlainTextResponse(service.policy_wording(), media_type="text/markdown")


@app.get("/api/company", operation_id="get_company")
def get_company() -> dict[str, Any]:
    """Get the company settings."""
    return service.get_company()


@app.get("/api/handlers", operation_id="list_handlers")
def list_handlers() -> list[dict[str, Any]]:
    """List the claims handlers."""
    return service.list_handlers()
