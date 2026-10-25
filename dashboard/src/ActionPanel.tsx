import { formatMoney } from "./format";
import type { ClaimDetail, Handler } from "./types";

interface ActionPanelProps {
  detail: ClaimDetail;
  handlers: Handler[];
  working: boolean;
  signingOff: boolean;
  selectedHandler: string;
  onHandlerChange: (handlerId: string) => void;
  onWork: () => void;
  onSignOff: () => void;
}

export function ActionPanel({
  detail,
  handlers,
  working,
  signingOff,
  selectedHandler,
  onHandlerChange,
  onWork,
  onSignOff,
}: Readonly<ActionPanelProps>) {
  if (detail.claim.status === "waiting") {
    return (
      <div className="action-panel">
        <div>
          <h3>Ready to work</h3>
          <p className="muted">
            Start the UnderCover Agent on this claim. The steps appear as it
            works.
          </p>
        </div>
        <button
          type="button"
          className="primary-button"
          onClick={onWork}
          disabled={working}
        >
          Work this claim
        </button>
      </div>
    );
  }

  if (detail.claim.status !== "awaiting_signoff") {
    return null;
  }

  const payout = detail.decision?.payout ?? 0;

  return (
    <div className="action-panel action-panel-blocked">
      <div>
        <h3>Waiting for sign-off</h3>
        <p className="signoff-payout">
          <span className="mono">{formatMoney(payout)}</span> payout
        </p>
        <p className="muted">
          The payment is blocked until a handler signs off.
        </p>
      </div>
      <div className="signoff-controls">
        <label htmlFor="handler-select">Handler</label>
        <select
          id="handler-select"
          value={selectedHandler}
          onChange={(event) => {
            onHandlerChange(event.target.value);
          }}
          disabled={signingOff}
        >
          {handlers.map((handler) => (
            <option key={handler.handler_id} value={handler.handler_id}>
              {handler.name} · {handler.role}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="secondary-button"
          onClick={onSignOff}
          disabled={signingOff || selectedHandler === ""}
        >
          Sign off
        </button>
      </div>
    </div>
  );
}
