"""Deterministic seed generator.

Emits CSV files to raw/, builds them as DuckDB tables in warehouse.duckdb
under schema `raw`, and renders DATA-123.md from DATA-123.md.tmpl with the
canonical reconciliation number.

Run via `make setup` (which also runs dbt full-refresh after this).
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
from faker import Faker

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
DB_PATH = ROOT / "warehouse.duckdb"
TEMPLATE_PATH = ROOT / "DATA-123.md.tmpl"
TICKET_PATH = ROOT / "DATA-123.md"

SEED = 20260517
START_DATE = datetime(2024, 11, 1)
END_DATE = datetime(2026, 5, 1)  # 18 months

N_MERCHANTS = 5_000
N_PRODUCTS = 500
N_ORDERS = 10_000

CUSTOMER_TYPES = ["B2B", "B2C", "MKT"]   # MKT is "marketplace"; intentionally undocumented
TIERS = ["STD", "ENT", "PLT"]            # standard / enterprise / platinum; intentionally undocumented


def random_dt(rng: random.Random, start: datetime, end: datetime) -> datetime:
    delta = end - start
    seconds = rng.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    RAW_DIR.mkdir(exist_ok=True)
    path = RAW_DIR / f"{name}.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def gen_merchants(rng: random.Random, fake: Faker) -> list[list]:
    rows = []
    for i in range(1, N_MERCHANTS + 1):
        rows.append([
            f"M{i:05d}",
            fake.company(),
            rng.choice(CUSTOMER_TYPES),
            rng.choice(TIERS),
            random_dt(rng, START_DATE - timedelta(days=365), START_DATE).isoformat(),
        ])
    return rows


def gen_products(rng: random.Random, fake: Faker) -> list[list]:
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        rows.append([
            f"P{i:04d}",
            fake.catch_phrase(),
            rng.randint(500, 50_000),  # list_price_in_cents
        ])
    return rows


@dataclass
class Order:
    order_id: str
    merchant_id: str
    customer_id: str
    order_status: str
    is_test: str           # "" (NULL) | "true" | "false"
    ordered_at: datetime
    paid_at: datetime | None
    shape: str             # "single" | "multi_full" | "partial" | "pending" | "cancelled"


@dataclass
class LineItem:
    line_item_id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price_in_cents: int
    line_status: str


@dataclass
class Shipment:
    shipment_id: str
    order_id: str
    shipped_at: datetime


@dataclass
class ShipmentLineItem:
    shipment_line_item_id: str
    shipment_id: str
    line_item_id: str
    quantity_shipped: int


def gen_orders_and_lines(
    rng: random.Random,
    products: list[list],
) -> tuple[list[Order], list[LineItem]]:
    """Generate orders + their line items. line_status defaults to 'pending' for
    pending/cancelled shapes; Task 5b overwrites it for shipped/partial shapes."""
    product_prices = {p[0]: p[2] for p in products}
    product_ids = list(product_prices.keys())

    orders: list[Order] = []
    lines: list[LineItem] = []
    next_line_id = 1

    for i in range(1, N_ORDERS + 1):
        order_id = f"O{i:06d}"
        merchant_id = f"M{rng.randint(1, N_MERCHANTS):05d}"
        customer_id = f"C{rng.randint(1, N_MERCHANTS * 4):06d}"

        # is_test: ~95% NULL (empty), ~3% true, ~2% false
        r = rng.random()
        if r < 0.95:
            is_test = ""
        elif r < 0.98:
            is_test = "true"
        else:
            is_test = "false"

        ordered_at = random_dt(rng, START_DATE, END_DATE - timedelta(days=14))

        s = rng.random()
        if s < 0.70:
            shape = "single"
        elif s < 0.82:
            shape = "multi_full"
        elif s < 0.90:
            shape = "partial"
        elif s < 0.95:
            shape = "pending"
        else:
            shape = "cancelled"

        # Order-level status + paid_at
        if shape == "cancelled":
            order_status = "cancelled"
            paid_at = None
            default_line_status = "cancelled"
        elif shape == "pending":
            order_status = "pending"
            paid_at = ordered_at + timedelta(minutes=rng.randint(1, 120))
            default_line_status = "pending"
        elif shape == "partial":
            order_status = "partially_shipped"
            paid_at = ordered_at + timedelta(minutes=rng.randint(1, 120))
            default_line_status = "pending"  # Task 5b overwrites per-line
        else:  # single, multi_full
            order_status = "shipped"
            paid_at = ordered_at + timedelta(minutes=rng.randint(1, 120))
            default_line_status = "fulfilled"  # Task 5b confirms

        # 1–4 line items per order, weighted toward 1–2
        n_lines = rng.choices([1, 2, 3, 4], weights=[40, 35, 20, 5])[0]
        for _ in range(n_lines):
            li_id = f"L{next_line_id:07d}"
            next_line_id += 1
            pid = rng.choice(product_ids)
            qty = rng.randint(1, 5)
            # unit_price = list_price * uniform(0.85, 1.0) — revenue isn't purely list price
            unit_price = int(product_prices[pid] * rng.uniform(0.85, 1.0))
            lines.append(LineItem(li_id, order_id, pid, qty, unit_price, default_line_status))

        orders.append(Order(
            order_id=order_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            order_status=order_status,
            is_test=is_test,
            ordered_at=ordered_at,
            paid_at=paid_at,
            shape=shape,
        ))

    return orders, lines


def gen_shipments(
    rng: random.Random,
    orders: list[Order],
    lines: list[LineItem],
) -> tuple[list[Shipment], list[ShipmentLineItem]]:
    """Build shipments + shipment_line_items per the per-order shape. Mutates
    lines[].line_status where the shape implies a non-default status (partials).
    Enforces invariant: sum(quantity_shipped per line) ≤ line.quantity."""
    lines_by_order: dict[str, list[LineItem]] = {}
    for li in lines:
        lines_by_order.setdefault(li.order_id, []).append(li)

    shipments: list[Shipment] = []
    ship_lines: list[ShipmentLineItem] = []
    next_ship_id = 1
    next_ship_line_id = 1

    for o in orders:
        if o.shape in ("pending", "cancelled"):
            continue  # no shipments

        order_lines = lines_by_order[o.order_id]

        if o.shape == "single":
            ship_dt = o.ordered_at + timedelta(days=rng.randint(1, 14))
            sid = f"S{next_ship_id:07d}"
            next_ship_id += 1
            shipments.append(Shipment(sid, o.order_id, ship_dt))
            for li in order_lines:
                ship_lines.append(ShipmentLineItem(
                    f"SL{next_ship_line_id:08d}", sid, li.line_item_id, li.quantity
                ))
                next_ship_line_id += 1
                li.line_status = "fulfilled"

        elif o.shape == "multi_full":
            # 2–3 shipments. First: 1–14 days; subsequent: 15–60 days after first.
            # 15–60 day gap forces month-boundary spread for many cases.
            ship_count = rng.choice([2, 3])
            first_dt = o.ordered_at + timedelta(days=rng.randint(1, 14))
            ship_dts = [first_dt]
            for _ in range(ship_count - 1):
                ship_dts.append(first_dt + timedelta(days=rng.randint(15, 60)))
            ship_dts = [min(d, END_DATE) for d in ship_dts]
            sids = []
            for dt in ship_dts:
                sid = f"S{next_ship_id:07d}"
                next_ship_id += 1
                sids.append(sid)
                shipments.append(Shipment(sid, o.order_id, dt))

            for li in order_lines:
                # Split qty across shipments. Last shipment takes the remainder.
                remaining = li.quantity
                for k, sid in enumerate(sids):
                    if k == len(sids) - 1:
                        take = remaining
                    else:
                        take = rng.randint(0, remaining)
                    if take > 0:
                        ship_lines.append(ShipmentLineItem(
                            f"SL{next_ship_line_id:08d}", sid, li.line_item_id, take
                        ))
                        next_ship_line_id += 1
                        remaining -= take
                li.line_status = "fulfilled"

        else:  # partial
            ship_dt = o.ordered_at + timedelta(days=rng.randint(1, 14))
            sid = f"S{next_ship_id:07d}"
            next_ship_id += 1
            shipments.append(Shipment(sid, o.order_id, ship_dt))

            for li in order_lines:
                pick = rng.choice(["full", "part", "pending"])
                if pick == "full":
                    ship_lines.append(ShipmentLineItem(
                        f"SL{next_ship_line_id:08d}", sid, li.line_item_id, li.quantity
                    ))
                    next_ship_line_id += 1
                    li.line_status = "fulfilled"
                elif pick == "part" and li.quantity > 1:
                    take = li.quantity - 1
                    ship_lines.append(ShipmentLineItem(
                        f"SL{next_ship_line_id:08d}", sid, li.line_item_id, take
                    ))
                    next_ship_line_id += 1
                    li.line_status = "pending"  # not fully fulfilled
                else:
                    # "pending" pick OR single-qty falling into "part" — leave unshipped
                    li.line_status = "pending"

    return shipments, ship_lines


def main() -> None:
    rng = random.Random(SEED)
    fake = Faker()
    Faker.seed(SEED)

    print("generating merchants...")
    write_csv(
        "merchants",
        ["merchant_id", "merchant_name", "customer_type", "tier", "merchant_created_at"],
        gen_merchants(rng, fake),
    )

    print("generating products...")
    write_csv(
        "products",
        ["product_id", "product_name", "list_price_in_cents"],
        gen_products(rng, fake),
    )

    print("generating orders + line items...")
    products_rows = []
    with (RAW_DIR / "products.csv").open() as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            products_rows.append([row[0], row[1], int(row[2])])
    orders, lines = gen_orders_and_lines(rng, products_rows)

    write_csv(
        "orders",
        ["order_id", "merchant_id", "customer_id", "order_status", "is_test",
         "ordered_at", "paid_at"],
        [[o.order_id, o.merchant_id, o.customer_id, o.order_status, o.is_test,
          o.ordered_at.isoformat(),
          o.paid_at.isoformat() if o.paid_at else ""] for o in orders],
    )
    write_csv(
        "line_items",
        ["line_item_id", "order_id", "product_id", "quantity",
         "unit_price_in_cents", "line_status"],
        [[li.line_item_id, li.order_id, li.product_id, li.quantity,
          li.unit_price_in_cents, li.line_status] for li in lines],
    )

    print("generating shipments...")
    shipments, ship_lines = gen_shipments(rng, orders, lines)

    # Re-write line_items since gen_shipments may have updated line_status
    write_csv(
        "line_items",
        ["line_item_id", "order_id", "product_id", "quantity",
         "unit_price_in_cents", "line_status"],
        [[li.line_item_id, li.order_id, li.product_id, li.quantity,
          li.unit_price_in_cents, li.line_status] for li in lines],
    )
    write_csv(
        "shipments",
        ["shipment_id", "order_id", "shipped_at"],
        [[s.shipment_id, s.order_id, s.shipped_at.isoformat()] for s in shipments],
    )
    write_csv(
        "shipment_line_items",
        ["shipment_line_item_id", "shipment_id", "line_item_id", "quantity_shipped"],
        [[sl.shipment_line_item_id, sl.shipment_id, sl.line_item_id, sl.quantity_shipped]
         for sl in ship_lines],
    )

    # Refunds added in later task.
    # DATA-123 render added in later task.

    print("done.")


if __name__ == "__main__":
    main()
