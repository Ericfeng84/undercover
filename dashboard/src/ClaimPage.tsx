import { useEffect, useState } from "react";
import { fetchClaim, workClaim } from "./api";
import { ClaimDetails } from "./ClaimDetails";
import { DecisionPanel } from "./DecisionPanel";
import { errorMessage, formatMoney, humanize } from "./format";
import { StatusChip } from "./StatusChip";
import { StepsPanel } from "./StepsPanel";
import type { ClaimDetail } from "./types";

interface ClaimPageProps {
  claimId: string;
  onBack: () => void;
}

export function ClaimPage({ claimId, onBack }: Readonly<ClaimPageProps>) {
  const [detail, setDetail] = useState<ClaimDetail | null>(null);
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const data = await fetchClaim(claimId);
        if (active) {
          setDetail(data);
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

      {claim.status === "waiting" && (
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
            onClick={() => void handleWork()}
            disabled={working}
          >
            Work this claim
          </button>
        </div>
      )}

      {working && claim.status === "in_progress" && (
        <p className="working" role="status">
          The agent is working on this claim...
        </p>
      )}

      <ClaimDetails detail={detail} />
      <DecisionPanel detail={detail} />
      <StepsPanel events={detail.events} />
    </section>
  );
}
