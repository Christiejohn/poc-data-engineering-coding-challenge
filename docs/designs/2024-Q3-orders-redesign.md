# Orders DW redesign — Q3 2024

**Author:** Sandra Patel (contractor)
**Status:** Implemented
**Last updated:** 2024-08-21

## Context

The legacy `orders_summary` view was a wide ad-hoc rollup written for the
2023 finance close. It lived on `staging` and was used directly by analytics —
six tools wrote against it. Two issues forced a rewrite:

1. Performance regressed in Q2 2024 once shipment volume crossed ~8M rows;
   refresh time pushed past the SLA.
2. Status reasoning was tangled with revenue reasoning. A bug fix in one
   half kept breaking the other.

## Decision

Split the wide view into a fact-style `order_fact` (one row per order) plus
a thin `order_line_fact` (one row per order line). Keep the merchant
attributes on a `lkp_merchants` lookup so the fact stays narrow.

`order_fact` materializes incrementally on `ordered_at` (via the
`get_incremental_value` macro) — refreshes are now O(new orders) rather than
O(all history).

## Out of scope (intentionally)

- Refunds. We don't load refund sources today; once we do, they belong in a
  separate `refund_fact` rather than collapsed onto `order_fact`. Putting
  refund logic on the order grain would re-create the "tangled status and
  revenue" problem we just untangled.
- Type 2 history on merchants. `lkp_merchants` is current-state only. If
  we need point-in-time merchant attributes (e.g. tier-at-time-of-order),
  that's a separate snapshot model.

## Reviewers

This design was reviewed at the Q3 design review (Aug 14). Open questions
that came up in review:

- *"Should `shipped_at` live on `order_fact`?"* — discussed, kept on the
  fact for now since most consumers want a single row per order. Open to
  revisiting if shipment-grain reporting becomes a thing.
- *"Test coverage on the join?"* — followed up in DATA-118 (added unique
  + not_null tests, did not add a row-level reconciliation).

## Follow-ups

- DATA-118: regression tests on order_fact join (closed)
- DATA-122: add source freshness on `raw.shipments` once upstream loader
  is reliable (open)
- DATA-145: refund sources (not yet scoped)
