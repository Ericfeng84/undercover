import { formatDateTime, formatMoney } from "./format";
import { Panel } from "./Panel";
import { OUTCOME_LABELS } from "./status";
import type { ClaimDetail, Decision } from "./types";

function paymentText(decision: Decision): string {
  if (decision.outcome !== "approve") {
    return "No payment.";
  }
  if (decision.paid_amount !== null && decision.paid_at !== null) {
    return `Paid ${formatMoney(decision.paid_amount)} on ${formatDateTime(
      decision.paid_at,
    )}.`;
  }
  return "Not paid.";
}

export function DecisionPanel({ detail }: Readonly<{ detail: ClaimDetail }>) {
  const { decision } = detail;

  return (
    <Panel title="Decision">
      {decision === null ? (
        <p className="muted">No decision yet.</p>
      ) : (
        <>
          <p className={`decision-outcome outcome-${decision.outcome}`}>
            {OUTCOME_LABELS[decision.outcome]}{" "}
            <span className="mono">{formatMoney(decision.payout)}</span>
          </p>
          <dl className="facts">
            <div>
              <dt>Calculation</dt>
              <dd>{decision.calculation}</dd>
            </div>
            <div>
              <dt>Reason</dt>
              <dd>{decision.reason}</dd>
            </div>
            <div>
              <dt>Policy section</dt>
              <dd>{decision.policy_section}</dd>
            </div>
            <div>
              <dt>Decided</dt>
              <dd>{formatDateTime(decision.decided_at)}</dd>
            </div>
          </dl>
          <p className="payment-state">{paymentText(decision)}</p>
        </>
      )}
    </Panel>
  );
}
