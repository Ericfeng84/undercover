import type { ClaimStatus, DecisionOutcome } from "./types";

export const STATUS_LABELS: Record<ClaimStatus, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  awaiting_signoff: "Waiting for sign-off",
  decided: "Decided",
};

export const STATUS_CLASSES: Record<ClaimStatus, string> = {
  waiting: "status-waiting",
  in_progress: "status-in-progress",
  awaiting_signoff: "status-awaiting-signoff",
  decided: "status-decided",
};

export const OUTCOME_LABELS: Record<DecisionOutcome, string> = {
  approve: "Approved",
  decline: "Declined",
  refer: "Referred",
};
