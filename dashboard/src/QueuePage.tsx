import { useEffect, useState } from "react";
import { fetchClaims } from "./api";
import { errorMessage, formatMoney, humanize } from "./format";
import { StatusChip } from "./StatusChip";
import type { ClaimSummary } from "./types";

interface QueuePageProps {
  onOpenClaim: (claimId: string) => void;
}

export function QueuePage({ onOpenClaim }: Readonly<QueuePageProps>) {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const data = await fetchClaims();
        if (active) {
          setClaims(data);
        }
      } catch (loadError) {
        if (active) {
          setError(errorMessage(loadError));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p className="muted">Loading claims...</p>;
  }

  if (error) {
    return (
      <div className="error" role="alert">
        {error}
      </div>
    );
  }

  return (
    <section>
      <div className="section-heading">
        <h2>Claims queue</h2>
        <p className="muted">{claims.length} claims</p>
      </div>
      <ul className="queue-list">
        {claims.map((claim) => (
          <li key={claim.claim_id}>
            <button
              type="button"
              className="queue-row"
              onClick={() => {
                onOpenClaim(claim.claim_id);
              }}
            >
              <span className="mono claim-id">{claim.claim_id}</span>
              <span className="queue-customer">{claim.customer_name}</span>
              <span>{humanize(claim.claim_type)}</span>
              <span className="mono">{formatMoney(claim.amount_claimed)}</span>
              <StatusChip status={claim.status} />
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
