import { formatMoney, humanize } from "./format";
import { Panel } from "./Panel";
import type { ClaimDetail } from "./types";

export function ClaimDetails({ detail }: Readonly<{ detail: ClaimDetail }>) {
  const { claim, policy, plan, customer } = detail;

  return (
    <div className="claim-grid">
      <div className="claim-main">
        <Panel title="The customer's story">
          <p className="story">{claim.story}</p>
        </Panel>

        <Panel title="Items claimed">
          <ul className="items">
            {claim.items.map((item) => (
              <li key={item.description}>
                <span>
                  {item.description}
                  <span className="muted item-category">
                    {humanize(item.category)}
                  </span>
                </span>
                <span className="mono">{formatMoney(item.amount)}</span>
              </li>
            ))}
          </ul>
          <p className="total">
            Total claimed
            <span className="mono">{formatMoney(claim.amount_claimed)}</span>
          </p>
        </Panel>

        <Panel title="Documents">
          <ul className="documents">
            {claim.documents.map((document) => (
              <li key={document.name}>
                <h4>{document.name}</h4>
                <p className="muted">{humanize(document.type)}</p>
                <p className="document-text">{document.content}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <aside className="claim-side">
        <Panel title="Customer">
          <dl className="facts">
            <div>
              <dt>Name</dt>
              <dd>{customer.name}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{customer.email}</dd>
            </div>
            <div>
              <dt>Phone</dt>
              <dd>{customer.phone}</dd>
            </div>
            <div>
              <dt>Address</dt>
              <dd>
                {customer.address.street}, {customer.address.city},{" "}
                {customer.address.state} {customer.address.zip}
              </dd>
            </div>
            <div>
              <dt>Customer since</dt>
              <dd>{customer.customer_since}</dd>
            </div>
          </dl>
        </Panel>

        <Panel title="Earlier claims">
          {customer.previous_claims.length === 0 ? (
            <p className="muted">No earlier claims.</p>
          ) : (
            <ul className="claim-history">
              {customer.previous_claims.map((previous) => (
                <li key={previous.claim_id}>
                  <p>
                    <span className="mono">{previous.claim_id}</span>{" "}
                    <span className="muted">{previous.filed_on}</span>
                  </p>
                  <p>{previous.summary}</p>
                  <p className="muted">
                    {humanize(previous.outcome)} ·{" "}
                    <span className="mono">
                      {formatMoney(previous.amount_paid)}
                    </span>
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Policy">
          <dl className="facts">
            <div>
              <dt>Policy</dt>
              <dd className="mono">{policy.policy_id}</dd>
            </div>
            <div>
              <dt>Plan</dt>
              <dd>{plan.name}</dd>
            </div>
            <div>
              <dt>Add-ons</dt>
              <dd>
                {policy.add_ons.length === 0
                  ? "None"
                  : policy.add_ons.map(humanize).join(", ")}
              </dd>
            </div>
            <div>
              <dt>Purchased</dt>
              <dd>{policy.purchased_on}</dd>
            </div>
            <div>
              <dt>Trip</dt>
              <dd>{policy.trip.destination}</dd>
            </div>
            <div>
              <dt>Travel dates</dt>
              <dd>
                {policy.trip.departs_on} to {policy.trip.returns_on}
              </dd>
            </div>
            <div>
              <dt>Trip cost</dt>
              <dd className="mono">{formatMoney(policy.trip.trip_cost)}</dd>
            </div>
            <div>
              <dt>Travelers</dt>
              <dd>{policy.travelers.join(", ")}</dd>
            </div>
          </dl>
        </Panel>

        <Panel title="Plan limits">
          <dl className="facts">
            <div>
              <dt>Trip cancellation maximum</dt>
              <dd className="mono">
                {formatMoney(plan.trip_cancellation_max)}
              </dd>
            </div>
            <div>
              <dt>Trip delay waiting period</dt>
              <dd>{plan.trip_delay_waiting_hours} hours</dd>
            </div>
            <div>
              <dt>Trip delay maximum</dt>
              <dd className="mono">{formatMoney(plan.trip_delay_max)}</dd>
            </div>
            <div>
              <dt>Baggage delay waiting period</dt>
              <dd>{plan.baggage_delay_waiting_hours} hours</dd>
            </div>
            <div>
              <dt>Baggage delay maximum</dt>
              <dd className="mono">{formatMoney(plan.baggage_delay_max)}</dd>
            </div>
            <div>
              <dt>Baggage and personal effects maximum</dt>
              <dd className="mono">{formatMoney(plan.baggage_max)}</dd>
            </div>
            <div>
              <dt>Per-item limit</dt>
              <dd className="mono">{formatMoney(plan.per_item_limit)}</dd>
            </div>
            <div>
              <dt>Passport maximum</dt>
              <dd className="mono">{formatMoney(plan.passport_max)}</dd>
            </div>
            <div>
              <dt>Emergency medical maximum</dt>
              <dd className="mono">
                {formatMoney(plan.emergency_medical_max)}
              </dd>
            </div>
            <div>
              <dt>Deductible</dt>
              <dd className="mono">{formatMoney(plan.deductible)}</dd>
            </div>
          </dl>
        </Panel>
      </aside>
    </div>
  );
}
