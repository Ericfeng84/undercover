import { STATUS_CLASSES, STATUS_LABELS } from "./status";
import type { ClaimStatus } from "./types";

export function StatusChip({ status }: Readonly<{ status: ClaimStatus }>) {
  return (
    <span className={`status-chip ${STATUS_CLASSES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}
