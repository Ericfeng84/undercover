export type ClaimStatus =
  "waiting" | "in_progress" | "awaiting_signoff" | "decided";

export type DecisionOutcome = "approve" | "decline" | "refer";

export interface ClaimSummary {
  claim_id: string;
  customer_name: string;
  claim_type: string;
  amount_claimed: number;
  summary: string;
  submitted_on: string;
  status: ClaimStatus;
}

export interface ClaimItem {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface Trip {
  destination: string;
  departs_on: string;
  returns_on: string;
  trip_cost: number;
}

export interface Policy {
  policy_id: string;
  customer_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  sold_through: string;
  trip: Trip;
  travelers: string[];
  status: string;
}

export interface Plan {
  plan: string;
  name: string;
  trip_cancellation_max: number;
  trip_delay_waiting_hours: number;
  trip_delay_max: number;
  baggage_delay_waiting_hours: number;
  baggage_delay_max: number;
  baggage_max: number;
  per_item_limit: number;
  passport_max: number;
  emergency_medical_max: number;
  deductible: number;
}

export interface PreviousClaim {
  claim_id: string;
  filed_on: string;
  incident_date: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
}

export interface Customer {
  customer_id: string;
  name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  address: Address;
  customer_since: string;
  previous_claims: PreviousClaim[];
}

export interface Claim {
  claim_id: string;
  policy_id: string;
  customer_id: string;
  claim_type: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: ClaimItem[];
  amount_claimed: number;
  documents: ClaimDocument[];
  status: ClaimStatus;
}

export interface Decision {
  outcome: DecisionOutcome;
  payout: number;
  calculation: string;
  reason: string;
  policy_section: string;
  decided_at: string;
  signed_off_by: string | null;
  signed_off_at: string | null;
  paid_amount: number | null;
  paid_at: string | null;
}

export interface ClaimEvent {
  id: number;
  claim_id: string;
  step: string;
  detail: string;
  created_at: string;
}

export interface ClaimDetail {
  claim: Claim;
  policy: Policy;
  plan: Plan;
  customer: Customer;
  decision: Decision | null;
  events: ClaimEvent[];
}

export interface Handler {
  handler_id: string;
  name: string;
  role: string;
  email: string;
  can_approve_over_limit: boolean;
}

export type View =
  | { kind: "queue" }
  | { kind: "claim"; claimId: string }
  | { kind: "instructions" };
