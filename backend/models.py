"""The API request bodies."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

CENTS = Decimal("0.01")


def whole_cents(value: Decimal) -> Decimal:
    """Reject an amount with more precision than cents."""
    if value != value.quantize(CENTS):
        raise ValueError("Amounts must be in whole cents")
    return value


Money = Annotated[Decimal, Field(ge=0), AfterValidator(whole_cents)]


class EventRequest(BaseModel):
    """A step to record on a claim."""

    step: str
    detail: str


class DecisionRequest(BaseModel):
    """A decision on a claim."""

    outcome: Literal["approve", "decline", "refer"]
    payout: Money
    calculation: str
    reason: str
    policy_section: str


class PayRequest(BaseModel):
    """A payment for an approved claim."""

    amount: Money


class SignOffRequest(BaseModel):
    """A handler's sign-off on an over-limit approval."""

    handler_id: str
