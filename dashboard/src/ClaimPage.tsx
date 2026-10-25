import { useEffect, useState } from "react";
import { fetchClaim, fetchHandlers, signOffClaim, workClaim } from "./api";
import { ActionPanel } from "./ActionPanel";
import { ClaimDetails } from "./ClaimDetails";
import { DecisionPanel } from "./DecisionPanel";
import { errorMessage, formatMoney, humanize } from "./format";
import { StatusChip } from "./StatusChip";
import { StepsPanel } from "./StepsPanel";
import type { ClaimDetail, Handler } from "./types";

interface ClaimPageProps {
  claimId: string;
  onBack: () => void;
}

export function ClaimPage({ claimId, onBack }: Readonly<ClaimPageProps>) {
  const [detail, setDetail] = useState<ClaimDetail | null>(null);
  const [handlers, setHandlers] = useState<Handler[]>([]);
  const [selectedHandler, setSelectedHandler] = useState("");
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);
  const [signingOff, setSigningOff] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [data, handlersData] = await Promise.all([
          fetchClaim(claimId),
          fetchHandlers(),
        ]);
        if (active) {
          setDetail(data);
          setHandlers(handlersData);
          setSelectedHandler(handlersData[0]?.handler_id ?? "");
        }
      } catch (loadError) {
        if (active) {
          setError(errorMessage(loadError));
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [claimId]);

  useEffect(() => {
    if (!working) {
      return;
    }

    const timer = window.setInterval(() => {
      void fetchClaim(claimId)
        .then((data) => {
          setDetail(data);
        })
        .catch((pollError: unknown) => {
          setError(errorMessage(pollError));
        });
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [claimId, working]);

  async function handleSignOff() {
    setError("");
    setSigningOff(true);
    try {
      const updated = await signOffClaim(claimId, selectedHandler);
      setDetail(updated);
    } catch (signOffError) {
      setError(errorMessage(signOffError));
      const refreshed = await fetchClaim(claimId).catch(() => null);
      if (refreshed !== null) {
        setDetail(refreshed);
      }
    } finally {
      setSigningOff(false);
    }
  }

  async function handleWork() {
    setError("");
    setWorking(true);
    setDetail((current) =>
      current === null
        ? current
        : { ...current, claim: { ...current.claim, status: "in_progress" } },
    );

    try {
      const updated = await workClaim(claimId);
      setDetail(updated);
    } catch (workError) {
      setError(errorMessage(workError));
      const refreshed = await fetchClaim(claimId).catch(() => null);
      if (refreshed !== null) {
        setDetail(refreshed);
      }
    } finally {
      setWorking(false);
    }
  }

  if (detail === null) {
    return (
      <section>
        <button type="button" className="back-button" onClick={onBack}>
          Back to queue
        </button>
        {error ? (
          <div className="error" role="alert">
            {error}
          </div>
        ) : (
          <p className="muted">Loading claim...</p>
        )}
      </section>
    );
  }

  const { claim, customer } = detail;

  return (
    <section className="claim-page">
      <div className="claim-top">
        <button type="button" className="back-button" onClick={onBack}>
          Back to queue
        </button>
        <span className="muted">
          Submitted {claim.submitted_on} · {claim.incident_location}
        </span>
      </div>

      <div className="claim-heading">
        <h2 className="mono">{claim.claim_id}</h2>
        <StatusChip status={claim.status} />
        <span>{customer.name}</span>
        <span className="muted">{humanize(claim.claim_type)}</span>
        <span className="mono">{formatMoney(claim.amount_claimed)}</span>
      </div>
      <p className="claim-summary">{claim.summary}</p>

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      <ActionPanel
        detail={detail}
        handlers={handlers}
        working={working}
        signingOff={signingOff}
        selectedHandler={selectedHandler}
        onHandlerChange={setSelectedHandler}
        onWork={() => void handleWork()}
        onSignOff={() => void handleSignOff()}
      />

      {working && claim.status === "in_progress" && (
        <p className="working" role="status">
          The agent is working on this claim...
        </p>
      )}

      <ClaimDetails detail={detail} />
      <DecisionPanel detail={detail} handlers={handlers} />
      <StepsPanel events={detail.events} />
    </section>
  );
}
