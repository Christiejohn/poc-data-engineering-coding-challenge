# PR Grading Rubric

**Internal only — do not share with candidates.** Use this to grade a candidate's PR for the Principal Data Engineer interview. Designed to be handed to a grading agent along with the PR diff and the interviewer's behavioral notes.

---

## How to use (instructions for the grading agent)

You are grading a Principal Data Engineer interview PR against this rubric. Inputs:

1. **The PR** — diff, commits, description, any committed design docs.
2. **Interviewer notes** — free-form observations from the live call (Section B inputs).
3. **Reference docs** for ground truth:
   - [`answer-key.md`](./answer-key.md) — canonical numbers and planted cases.
   - [`technical-interview-design.md`](./technical-interview-design.md) — design rationale.
   - `DATA-123.md` (in repo root) — the candidate's ticket.

**Process:**
1. Read the PR end-to-end before scoring.
2. Score each criterion 1–5 using the anchors below. Cite specific files/lines as evidence.
3. Compute the totals and apply the recommendation rule.
4. Produce the output in the format at the bottom of this file.
5. Be honest about uncertainty — if a criterion isn't gradable from the PR, say so.

**Scoring anchors (apply to every criterion):**

| Score | Meaning |
|---|---|
| 1 | Missing or wrong. The PR shows no engagement with this dimension, or actively works against it. |
| 2 | Partial / surface-level. Acknowledged but not addressed substantively. |
| 3 | Acceptable. Meets the senior-engineer bar. |
| 4 | Strong. Above bar — clear thought, solid execution. |
| 5 | Exemplary. Principal-level signal — names the deeper issue, makes a non-obvious right call, or demonstrates rare judgment. |

---

## Section A — PR-observable criteria

These are graded from the PR diff alone. The grading agent should be able to score these without interviewer input.

### A1. Problem 1 — Bug diagnosis & fix correctness *(gatekeeper)*

Did the candidate fix the grain bug in `models/orders/dw/order_fact.sql`?

| Score | Anchor |
|---|---|
| 1 | Bug not fixed; reconciliation still off; or fix breaks other models. |
| 2 | Fix produces correct totals but mechanism is unclear or fragile (e.g., changes the test instead of the model). |
| 3 | **Acceptable tier**: replaces `qualify` with `sum(...) over (partition by order_id)` or equivalent — surgical one-line fix. Correct totals, comment updated. |
| 4 | **Senior tier**: separates concerns into distinct CTEs — one for `order_revenue` from line items, one for `order_first_ship` from shipments. Joins cleanly. |
| 5 | **Principal tier**: recognizes `shipped_at` doesn't belong on an order-grain fact at all. Proposes (or implements) moving shipment metadata to a `shipment_fact`; `order_fact` carries only derivations like `first_shipped_at = min(shipped_at)`. |

**Verify:** `sum(revenue) where not coalesce(is_test, false)` should equal the value in [`answer-key.md`](./answer-key.md) under "True reconciled non-test revenue".

**Gatekeeper rule:** A1 < 3 → no hire regardless of other scores.

### A2. Problem 1 — Test hygiene

What did the candidate do with the warn-level reconciliation test (`tests/order_fact_revenue_reconciliation.sql`) and what regression coverage did they add?

| Score | Anchor |
|---|---|
| 1 | Removed, weakened, or ignored the warn test. No new tests. |
| 2 | Left the warn at `warn` severity. No new tests. |
| 3 | Escalated the existing test from `warn` → `error` post-fix. No new tests. |
| 4 | Escalated to `error` AND added at least one new test (e.g., a row-level parity check) covering the regression. |
| 5 | Wrote a row-level parity invariant (per-order revenue == sum of its line items) as a generic/reusable test, escalated severity, and the test would have caught the original bug. |

### A3. Problem 2 — Refund model structure (graded from the plan, not the code)

**Q2 is presentation-graded.** The candidate is presenting a plan to finance analytics for how DE would model refunds. Building the models is bonus. Score the **plan** they walk through — the rubric below applies whether the artifact is markdown, slides, a whiteboard photo, or SQL stubs with commentary.

Did the candidate's plan propose a `refund_fact` model rather than dumping refund columns onto `order_fact`?

| Score | Anchor |
|---|---|
| 1 | Plan crams refund logic into `order_fact` with no separate model; conflates allocation concerns. |
| 2 | Plan describes a single refund model that conflates line / tender / source concerns. |
| 3 | Plan proposes a separate `refund_fact` (or equivalent) at a defensible grain, with clean joins to `order_fact`/`order_line_fact` described. |
| 4 | Plan justifies the `refund_fact` grain explicitly; describes an `order_line_fact.refunded_amount` column populated via stated allocation logic. |
| 5 | Plan describes a layered model: a raw `refund_fact` preserving source grain, plus derived columns on order/line facts via documented allocation. Articulates raw refunds and allocated refunds as different artifacts and explains why. |

**Code bonus (additive, no penalty for absent):** If the candidate also shipped working code matching their plan, +0.5 to this criterion's score (capped at 5). Code that contradicts the plan or is half-built earns nothing extra — the plan is the deliverable.

### A4. Problem 2 — Allocation decomposition (graded from the plan)

Does the candidate's plan decompose the three orthogonal allocation concerns?

Strong candidates may also flag that cancellations are a separate concern from refunds — cancelled lines never had revenue (cancellation is pre-fulfillment), so they're not part of "net revenue minus refunds". This is credited as bonus signal in A5; A4 grades the three concerns below.

The three concerns:
1. **Line allocation** — when refund hits at order grain but lines exist (Stripe, internal POS), how to populate `order_line_fact.refunded`.
2. **Tender allocation** — split-tender refunds. **Note:** all refunds (including store credit) net against revenue per current finance guidance; tender allocation is about *tracking* the split for reconciliation, not about whether store credit reduces the headline number.
3. **Source reconciliation** — same logical refund across `refunds_shopify` / `refunds_stripe` / `refunds_internal_pos`, no shared ID.

| Score | Anchor |
|---|---|
| 1 | None of the three named or addressed. |
| 2 | One of three addressed (typically tender, since Jamie volunteers it). |
| 3 | Two of three named with a stated approach. |
| 4 | All three named, each with a stated approach and tradeoffs articulated to finance. |
| 5 | All three named as *orthogonal* concerns (the principal-level insight), with explicit testable invariants for each (e.g., "sum of allocated line refunds == order refund total"), and the candidate can defend the choices when finance pushes back. |

### A5. Problem 2 — Planted refund cases (graded from the plan)

Does the candidate's plan correctly handle (or explicitly call out as testable cases) the planted refund patterns listed in [`answer-key.md`](./answer-key.md)?

The expected treatment for each pattern:

| Pattern | Expected treatment in the plan |
|---|---|
| Shopify partial-line refund | Line-level refund flows through to the refunded line only |
| Internal POS order-level refund (line statuses still `fulfilled`) | Cancel-vs-refund nuance named; refund applied without changing line status |
| `shopify_stripe` split-tender (card + store_credit) | All refund dollars (card + store_credit) net against revenue. Tender split preserved for reconciliation/tracking, not used to exclude store credit from the headline. **Multiple instances planted** — see [`answer-key.md`](./answer-key.md). |

**Use [`answer-key.md`](./answer-key.md) for the canonical order IDs, amounts, and instance counts** — they regenerate when seeds change.

| Score | Anchor |
|---|---|
| 1 | None named or addressed in the plan. |
| 2 | One pattern named. |
| 3 | Two patterns named with a stated approach. |
| 4 | All three patterns named with stated approach; any deferrals have rationale. |
| 5 | All three named as testable cases with explicit invariants the candidate can articulate to finance. Bonus signal if they also flag the cancellations-vs-refunds distinction. |

**Common miss to flag:** if the plan treats store credit as *excluding* refunds from the headline number, that's the **old** rule — current guidance is that all refunds (including store credit) net against revenue. Mark down accordingly and note in feedback.

### A6. Scoping & artifact quality (presentation-graded)

Q2's deliverable is the plan + walkthrough for finance analytics. Score the artifact + how the candidate framed scope.

| Score | Anchor |
|---|---|
| 1 | No coherent artifact; walkthrough is rambling or contradicts itself; no scope discipline. |
| 2 | Artifact exists but is unclear, internally inconsistent, or assumes engineering vocabulary the finance audience doesn't have. |
| 3 | Clear plan tailored to a finance audience. What's in scope vs. deferred is named. |
| 4 | Clear plan with a deliberate "clean slice" called out (e.g., "Shopify-only `refund_fact` first") and documented assumptions + open questions. |
| 5 | Plan tailored to finance, surfaces assumptions and open questions, distinguishes prod-blockers from deferrable concerns, AND the candidate can defend choices live when finance pushes back. Bonus signal if they also shipped code matching the plan. |

### A7. Boy scout finds *(bonus, +0 to +3 to total)*

Realism props planted around the repo. Bonus only — no penalty for missing.

Cheap-tier finds available:
- Stale TODO on an unrelated model
- Commented-out source freshness config
- sqlfluff nits on non-`order_fact` files
- Undocumented columns in `models/*.yml`
- Order/line status mismatches surfaced via the same audit lens (planted on `O000001`–`O000008`; canonical list in [`answer-key.md`](./answer-key.md))

| Bonus | Anchor |
|---|---|
| +0 | None addressed. |
| +1 | One or two unrelated finds fixed in the PR. |
| +2 | Three+ finds, or one find paired with documentation explaining the systemic issue. |
| +3 | Identifies the *category* (e.g., "we have stale config across the orders project") and proposes a sweep, not just a one-off fix. |

---

## Section B — Interviewer-observed criteria

These cannot be graded from the PR. The interviewer fills in observations during/after the call; the grading agent scores Section B from those notes.

Interviewer notes should follow the template at the bottom of [`interviewer.md`](./interviewer.md#after-the-call).

If interviewer notes are absent, mark each B criterion as "not graded — no observations provided" rather than guessing.

### B1. AI-prompting maturity

Did the candidate orchestrate the AI's investigation, or type `fix this` and watch?

| Score | Anchor |
|---|---|
| 1 | Typed terse commands (`fix this`, `find the bug`); accepted first AI output without verification. |
| 2 | Multi-step prompts but no verification step; accepted AI claims without checking source. |
| 3 | Explore → act → verify cycle visible. Pushed back on at least one wrong AI claim. |
| 4 | Prompted AI to read conventions / prior designs before acting. Verified factual claims against source. Iterated on prompts when results were off. |
| 5 | Treated AI as a junior engineer to be supervised: explore the codebase, explain before changing, propose options before implementing. Caught and corrected at least one AI hallucination. |

### B2. Asks vs assumes

Did the candidate ask Jamie / clarify undocumented columns, or reflexively assume?

| Score | Anchor |
|---|---|
| 1 | Zero questions asked. Made silent assumptions on every ambiguity. |
| 2 | One low-quality question (e.g., "what's the goal?"). |
| 3 | Asked at least one substantive question before writing P2 code. |
| 4 | Asked multiple substantive questions; surfaced assumptions explicitly even when not asking. |
| 5 | Asked questions that *re-shaped* the approach (e.g., asked about store-credit treatment before designing tender allocation). Surfaced assumptions in the PR/design doc with rationale. |

### B3. Mode-switching

P2's framing now tells the candidate that the deliverable is a plan/walkthrough and that code is bonus. The mode-switching test is no longer "did they realize this isn't a code problem" — that's given. The test is: did they actually invest in *thinking through the modeling* (decomposition, tradeoffs, stakeholder framing), or did they treat the plan as a thin wrapper around "let me write some SQL"?

| Score | Anchor |
|---|---|
| 1 | Ignored the framing; jumped straight to SQL with no plan articulated. The "presentation" was a code walkthrough. |
| 2 | Built a thin plan as scaffolding for code; little evidence of thinking about modeling tradeoffs. |
| 3 | Plan + code in roughly equal measure; some decomposition visible, some decisions explained. |
| 4 | Invested in the plan first; modeling decisions are explained with alternatives considered; code (if shipped) supports the plan rather than driving it. |
| 5 | Spent the time on modeling judgment — decomposed orthogonal concerns, articulated tradeoffs to a finance audience, anticipated pushback. Whether they shipped code or not is incidental to the score. |

---

## Recommendation

### Compute totals

- **Section A total** (out of 30): A1 + A2 + A3 + A4 + A5 + A6
- **Section B total** (out of 15): B1 + B2 + B3
- **Combined** (out of 45): Section A + Section B
- **With bonus** (out of 48): Combined + A7

### Recommendation rule

Apply in order — first match wins:

| Recommendation | Rule |
|---|---|
| **No hire** | A1 < 3 (gatekeeper failed) — regardless of other scores. |
| **No hire** | Combined < 25. |
| **Lean no hire** | Combined 25–29, OR any criterion at 1. |
| **Lean hire** | Combined 30–34, no criterion at 1, A1 ≥ 3. |
| **Hire** | Combined 35–39. |
| **Strong hire (Principal)** | Combined ≥ 40 AND at least two criteria at 5 across A1, A3, A4, A6 (the principal-signal criteria). |

The bonus (A7) does not change the recommendation tier on its own but is reported alongside.

---

## Output format (what the grading agent should produce)

```markdown
# PR Grading — <candidate name / PR link>

## Summary
- **Recommendation:** <No hire | Lean no hire | Lean hire | Hire | Strong hire>
- **Combined:** XX/45 (+X bonus)
- **Section A:** XX/30 — **Section B:** XX/15

## Section A — PR-observable
| Criterion | Score | Evidence |
|---|---|---|
| A1. P1 bug fix | X/5 | `models/orders/dw/order_fact.sql:LL` — <brief> |
| A2. Test hygiene | X/5 | `tests/...:LL` — <brief> |
| A3. Refund model structure | X/5 | <files/lines> — <brief> |
| A4. Allocation decomposition | X/5 | <files/lines> — <brief> |
| A5. Planted refund cases | X/5 | <which handled> |
| A6. Scoping & artifact quality | X/5 | <brief> |
| A7. Boy scout (bonus) | +X/3 | <finds> |

## Section B — Interviewer-observed
| Criterion | Score | Evidence from notes |
|---|---|---|
| B1. AI-prompting maturity | X/5 | <quote/paraphrase> |
| B2. Asks vs assumes | X/5 | <quote/paraphrase> |
| B3. Mode-switching | X/5 | <quote/paraphrase> |

## Strengths
- <bullet>

## Concerns
- <bullet>

## Open questions for the interviewer
- <anything the PR + notes didn't resolve>
```
