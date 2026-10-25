import { formatDateTime } from "./format";
import { Panel } from "./Panel";
import type { ClaimEvent } from "./types";

export function StepsPanel({ events }: Readonly<{ events: ClaimEvent[] }>) {
  return (
    <Panel title="Steps">
      {events.length === 0 ? (
        <p className="muted">No steps yet.</p>
      ) : (
        <ol className="steps">
          {events.map((event) => (
            <li key={event.id}>
              <div className="step-heading">
                <span className="step-name">{event.step}</span>
                <span className="mono muted">
                  {formatDateTime(event.created_at)}
                </span>
              </div>
              <p>{event.detail}</p>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  );
}
