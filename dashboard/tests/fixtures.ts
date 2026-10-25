import { vi } from "vitest";
import type {
  ClaimDetail,
  ClaimEvent,
  ClaimStatus,
  ClaimSummary,
  Decision,
  Handler,
} from "../src/types";

const baseClaim: ClaimDetail["claim"] = {
  claim_id: "CLM-1001",
  policy_id: "POL-2001",
  customer_id: "CUS-3001",
  claim_type: "trip_delay",
  submitted_on: "2026-06-24",
  incident_date: "2026-06-18",
  incident_location: "Rome, Italy",
  summary: "Flight home canceled by the airline, rebooked the next morning",
  story:
    "My flight home from Rome on June 18 was canceled by Meridian Air about two hours before departure.",
  items: [
    {
      description: "Airport hotel, one night",
      category: "accommodation",
      amount: 245,
    },
    { description: "Dinner and breakfast", category: "meals", amount: 95 },
    {
      description: "Taxis between the airport and the hotel",
      category: "transport",
      amount: 80,
    },
  ],
  amount_claimed: 420,
  documents: [
    {
      name: "Meridian Air cancellation notice",
      type: "carrier_report",
      content: "Flight MA 611 was canceled because of crew availability.",
    },
    {
      name: "Hotel receipt",
      type: "receipt",
      content: "Hotel Aurelia Fiumicino. Total paid: $245.00.",
    },
    {
      name: "Meal receipts",
      type: "receipt",
      content: "Dinner and breakfast. Total: $95.00.",
    },
    {
      name: "Taxi receipts",
      type: "receipt",
      content: "Two taxi journeys. Total: $80.00.",
    },
  ],
  status: "waiting",
};

const baseDetail: Omit<ClaimDetail, "claim" | "decision" | "events"> = {
  policy: {
    policy_id: "POL-2001",
    customer_id: "CUS-3001",
    plan: "premium",
    add_ons: [],
    purchased_on: "2026-04-22",
    sold_through: "Meridian Air checkout",
    trip: {
      destination: "Rome, Italy",
      departs_on: "2026-06-10",
      returns_on: "2026-06-18",
      trip_cost: 3100,
    },
    travelers: ["Maya Patel"],
    status: "active",
  },
  plan: {
    plan: "premium",
    name: "UnderCover Premium",
    trip_cancellation_max: 5000,
    trip_delay_waiting_hours: 6,
    trip_delay_max: 800,
    baggage_delay_waiting_hours: 12,
    baggage_delay_max: 300,
    baggage_max: 1500,
    per_item_limit: 300,
    passport_max: 250,
    emergency_medical_max: 100000,
    deductible: 50,
  },
  customer: {
    customer_id: "CUS-3001",
    name: "Maya Patel",
    email: "maya.patel@example.com",
    phone: "+1 201 555 0143",
    date_of_birth: "1988-03-14",
    address: {
      street: "48 Wayne Street, Apt 5C",
      city: "Jersey City",
      state: "NJ",
      zip: "07302",
    },
    customer_since: "2023-04-11",
    previous_claims: [
      {
        claim_id: "CLM-0412",
        filed_on: "2024-08-19",
        incident_date: "2024-08-09",
        claim_type: "baggage_delay",
        summary: "Checked bag arrived 30 hours late in Lisbon",
        outcome: "approved",
        amount_paid: 140,
      },
    ],
  },
};

interface DetailOptions {
  status?: ClaimStatus;
  decision?: Decision | null;
  events?: ClaimEvent[];
}

export function claimDetail(options: DetailOptions = {}): ClaimDetail {
  return {
    ...baseDetail,
    claim: { ...baseClaim, status: options.status ?? "waiting" },
    decision: options.decision ?? null,
    events: options.events ?? [],
  };
}

export function decision(overrides: Partial<Decision> = {}): Decision {
  return {
    outcome: "approve",
    payout: 250,
    calculation: "Eligible costs less the deductible.",
    reason: "The policy wording covers the delay.",
    policy_section: "Section 3 and Section 10",
    decided_at: "2026-07-01T12:00:00Z",
    signed_off_by: null,
    signed_off_at: null,
    paid_amount: null,
    paid_at: null,
    ...overrides,
  };
}

export function claimEvent(
  id: number,
  step: string,
  detail: string,
  createdAt = "2026-07-01T12:00:00Z",
): ClaimEvent {
  return {
    id,
    claim_id: "CLM-1001",
    step,
    detail,
    created_at: createdAt,
  };
}

export function queueSummaries(): ClaimSummary[] {
  return Array.from({ length: 25 }, (_, index) => ({
    claim_id: `CLM-${String(1001 + index)}`,
    customer_name: index === 0 ? "Maya Patel" : `Customer ${String(index + 1)}`,
    claim_type: "trip_delay",
    amount_claimed: 420,
    summary: "Flight home canceled by the airline, rebooked the next morning",
    submitted_on: "2026-06-24",
    status: "waiting",
  }));
}

export const handlers: Handler[] = [
  {
    handler_id: "HND-01",
    name: "Dana Whitfield",
    role: "Senior Claims Handler",
    email: "dana.whitfield@undercover.example",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-02",
    name: "Marcus Oyelaran",
    role: "Claims Handler",
    email: "marcus.oyelaran@undercover.example",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-03",
    name: "Priya Raman",
    role: "Claims Handler",
    email: "priya.raman@undercover.example",
    can_approve_over_limit: true,
  },
];

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function textResponse(text: string): Response {
  return new Response(text, {
    status: 200,
    headers: { "Content-Type": "text/markdown" },
  });
}

type Route = () => Response | Promise<Response>;

function urlOf(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  return input.url;
}

export function routeFetch(routes: Record<string, Route | undefined>) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = urlOf(input);
    const route = routes[url];
    if (route === undefined) {
      return Promise.resolve(
        jsonResponse({ detail: `No mock for ${url}` }, 404),
      );
    }
    return Promise.resolve(route());
  });
}
