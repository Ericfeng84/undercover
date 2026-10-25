"""The SQLite database and its seed data."""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / ".data" / "undercover.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    submitted_on TEXT NOT NULL,
    incident_date TEXT NOT NULL,
    incident_location TEXT NOT NULL,
    summary TEXT NOT NULL,
    story TEXT NOT NULL,
    items TEXT NOT NULL,
    amount_claimed REAL NOT NULL,
    documents TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    add_ons TEXT NOT NULL,
    purchased_on TEXT NOT NULL,
    sold_through TEXT NOT NULL,
    trip TEXT NOT NULL,
    travelers TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    address TEXT NOT NULL,
    customer_since TEXT NOT NULL,
    previous_claims TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS company (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS handlers (
    handler_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT NOT NULL,
    can_approve_over_limit INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    claim_id TEXT PRIMARY KEY REFERENCES claims(claim_id),
    outcome TEXT NOT NULL,
    payout_cents INTEGER NOT NULL,
    calculation TEXT NOT NULL,
    reason TEXT NOT NULL,
    policy_section TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    signed_off_by TEXT REFERENCES handlers(handler_id),
    signed_off_at TEXT,
    paid_amount_cents INTEGER,
    paid_at TEXT
);

CREATE TABLE IF NOT EXISTS claim_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
    step TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def database_path() -> Path:
    """Return the database path from DATABASE_PATH, or the local default."""
    configured = os.getenv("DATABASE_PATH")
    return Path(configured) if configured else DEFAULT_DATABASE_PATH


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open one connection, committing when the block succeeds."""
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    """Create the schema and seed it when the queue is empty."""
    with connect() as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        if count == 0:
            seed(connection)


def read_data(filename: str) -> Any:
    """Read one of the business data files."""
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def seed(connection: sqlite3.Connection) -> None:
    """Load the queue data into an empty database."""
    claims = read_data("claims.json")
    connection.executemany(
        """
        INSERT INTO claims (
            claim_id, policy_id, customer_id, claim_type, submitted_on,
            incident_date, incident_location, summary, story, items,
            amount_claimed, documents, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                claim["claim_id"],
                claim["policy_id"],
                claim["customer_id"],
                claim["claim_type"],
                claim["submitted_on"],
                claim["incident_date"],
                claim["incident_location"],
                claim["summary"],
                claim["story"],
                json.dumps(claim["items"]),
                claim["amount_claimed"],
                json.dumps(claim["documents"]),
                "waiting",
            )
            for claim in claims
        ],
    )

    policies = read_data("policies.json")
    connection.executemany(
        """
        INSERT INTO policies (
            policy_id, customer_id, plan, add_ons, purchased_on,
            sold_through, trip, travelers, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                policy["policy_id"],
                policy["customer_id"],
                policy["plan"],
                json.dumps(policy["add_ons"]),
                policy["purchased_on"],
                policy["sold_through"],
                json.dumps(policy["trip"]),
                json.dumps(policy["travelers"]),
                policy["status"],
            )
            for policy in policies
        ],
    )

    customers = read_data("customers.json")
    connection.executemany(
        """
        INSERT INTO customers (
            customer_id, name, email, phone, date_of_birth,
            address, customer_since, previous_claims
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                customer["customer_id"],
                customer["name"],
                customer["email"],
                customer["phone"],
                customer["date_of_birth"],
                json.dumps(customer["address"]),
                customer["customer_since"],
                json.dumps(customer["previous_claims"]),
            )
            for customer in customers
        ],
    )

    connection.execute(
        "INSERT INTO plans (id, data) VALUES (1, ?)",
        (json.dumps(read_data("plans.json")),),
    )
    connection.execute(
        "INSERT INTO company (id, data) VALUES (1, ?)",
        (json.dumps(read_data("company.json")),),
    )

    handlers = read_data("handlers.json")
    connection.executemany(
        """
        INSERT INTO handlers (
            handler_id, name, role, email, can_approve_over_limit
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                handler["handler_id"],
                handler["name"],
                handler["role"],
                handler["email"],
                handler["can_approve_over_limit"],
            )
            for handler in handlers
        ],
    )
