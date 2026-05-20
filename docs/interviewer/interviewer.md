# Interviewer Run Sheet

**Internal only — do not share with candidates.** Use this *during* the live 60-minute Principal Data Engineer interview. Post-call PR grading lives in [`pr-grading-rubric.md`](./pr-grading-rubric.md).

<!-- MAINTAINER NOTE: The reconciliation amount $12,989,886.01 is hardcoded in
two places below — Jamie's Q&A row and the Problem 1 opening script. If you
regenerate seeds (`make seed`), update both to match `answer-key.md`. -->

---

## Before the call (~10 min)

1. **Instruct the candidate to clone the repo and run setup:**
   ```bash
   uv sync
   make setup
   ```
   Candidate runs this; you do not need to.

2. **Onboarding (one-time):** read [`technical-interview-design.md`](./technical-interview-design.md) and [`pr-grading-rubric.md`](./pr-grading-rubric.md) once.

---

## Time budget (60 min)

| Minutes | Phase | Notes |
|---|---|---|
| 0–5 | Setup & orient | Candidate reads `README.md` and `DATA-123.md`. Don't fill silence. |
| 5–20 | Problem 1 (grain bug) | **Target: ~15 min.** If still working at 20, let it run to ~30 — but it eats P2 time. 25+ min on P1 = "struggling against the floor." |
| 20–55 | Problem 2 (refunds) | **Protect this block.** P2 is the design problem and the Principal signal. Asymmetric budget is deliberate. |
| 55–60 | Wrap + candidate Qs | Hard stop. |

P1 sets a code-shipping rhythm; P2 deliberately breaks it. **Whether the candidate notices the shape change is itself the test.**

---

## Playing Jamie & Finance Analytics

Jamie is a senior finance analyst available on Slack during the interview. They have basic data-modeling vocabulary (knows what grain, fact, dim mean), strong opinions on what counts as revenue, and limited patience for SQL. They know Stripe is the source of truth for cash and don't track what Shopify reports independently.

**Default posture:**
- **Silent unless asked.** Respond when the candidate messages you; do not volunteer. Reflexively reaching for the stakeholder is itself a discriminator.
- **Do not lead** to the bug, to "write a design doc", or to ambient signals.
- **Out-of-scope deflections:** tax, shipping refunds beyond "net of shipping", the unloaded Stripe payment export, any merchant outside the seeded set.

**What to avoid:**
- Don't lead the candidate to the bug. ("Did you check the qualify line?" — never.)
- Don't lead the candidate to "write a design doc." If they ask whether one's expected, you can confirm yes — but don't suggest it unprompted.
- If the candidate asks about something the answer-key or design doc marks as out-of-scope, say so.

**If asked, respond verbatim (or close to it):**

| Candidate asks | Jamie says |
|---|---|
| *"What do you mean by net revenue?"* | "Good question. Headline number is gross revenue net of refunds — gross of tax, net of refunds. I'm honestly not sure on shipping refunds — proceed assuming net of shipping for now." |
| *"Should cancelled lines reduce gross revenue?"* | "Cancellations are pre-fulfillment in the normal lifecycle — those lines were never going to land as revenue, so they're not in gross. Refunds are different: post-fulfillment, post-payment. If you see a cancelled line on an order that already shipped, that's a data-quality issue worth flagging separately, not a refund." |
| *"Should store-credit refunds reduce revenue?"* | "Yes — net them against revenue same as cash. Store credit going out the door is still a refund. Tender type matters for tracking and reconciliation, but not for the headline number." |
| *"How do we handle the merchant on internal POS where we don't have line-level data?"* | "Honest answer? I don't know yet. What are the options?" |
| *"Do we have payment data to reconcile original tender against refund tender?"* | "Yes, but it's in a separate Stripe export we haven't loaded yet — out of scope for this iteration." |
| *"What's the expected reconciliation number?"* (P1) | "My captures show \$12,989,886.01 for real merchants in the relevant period." |
| *"Is a design doc expected?"* | "Yeah, this team usually does design review before non-trivial work hits prod. There's a doc Sandra wrote in Q3 (`docs/designs/2024-Q3-orders-redesign.md`) that's a good template." |
| *"For the refunds work — should we also account for cancellations in net revenue?"* | "Good catch. Cancellations and refunds are both ways money doesn't ultimately land, but they happen at different points in the lifecycle. We asked for refunds because that's the gap finance is currently feeling. Cancellations are worth flagging in your plan even if they're not the immediate ask." |

---

## Problem 1 — the grain bug

**Opening script (verbatim, after candidate has read `README.md` and `DATA-123.md`):**

> *"Q1 live gross revenue from real merchants is coming in below our Stripe captures of ~\$12,989,886.01. Can you take a look at `order_fact`?"*

Then stop. Do not say where the bug is. Do not mention `dbt test`.

**Cross-check data:**
- Bug location: `models/orders/dw/order_fact.sql` — revenue computed by `qualify`-ing at the wrong grain.
- True non-test revenue after fix: see [`answer-key.md`](./answer-key.md).
- Verify with: `make sql Q="select sum(revenue) from main_orders_dw.order_fact where not coalesce(is_test, false)"`
- Reconciliation test passing (was warn): `make test`

**Watch for (jot in notes for post-call rubric):**
- Did they run `dbt test` before editing, or dive in?
- What did they do with the warn-level test? (Investigated / shrugged / escalated to error.)
- Did they write a row-level parity regression test?
- Did they identify the `shipped_at`-on-order-fact architectural smell? *(Top-tier principal signal.)*
- Did they ask Jamie about cancelled lines, or assume? (Cancelled-line treatment is undocumented in the model — strong asks-vs-assumes signal.)

---

## Problem 2 — refunds across messy sources

**Opening script (verbatim, transitioning from P1):**

> *"Okay, let's move on. Finance needs net revenue. Your task is to put together a plan for how data engineering would model refunds — surface refund totals on `order_fact` and per-line refund amounts on `order_line_fact`. Before we make changes, we want to walk finance analytics through the plan and explain the major modeling decisions. I'll be playing finance analytics. Building the models is bonus — what we mainly want is the plan and the walkthrough. Jamie from finance analytics is available on Slack if you have questions."*

Then stop. Do not add context. Do not say "write a design doc." Do not say "this one's more open-ended." Silence is load-bearing.

The framing matters: AI can write good code — that's not what we're testing. We're testing **how the candidate makes modeling design decisions** and communicates them to a non-engineer stakeholder. Code is a bonus, not the deliverable.

**Closing deliverable ask (~5 min left, or when they're wrapping up):**

> *"Walk us through your plan as if I'm finance analytics. What are you proposing, and what are the major decisions you made along the way?"*

Format-neutral on artifact (markdown, whiteboard, slides, walking through SQL all valid) but the **presentation + decision rationale is the deliverable**. Code shipped is bonus signal on top.

**Cross-check data:** Cross-check candidate's plan against the planted refund cases in [`answer-key.md`](./answer-key.md). Patterns the plan should address (handled, or named as testable cases): Shopify partial-line refund, internal_pos order-level refund (line statuses still 'fulfilled'), shopify_stripe split-tender (card + store_credit).

Status mismatches in the `O000001`–`O000008` range are planted separately (order/line status conflicts) — see [`answer-key.md`](./answer-key.md) for the canonical list. Bonus if the candidate surfaces them.

**Watch for (jot in notes for post-call rubric):**
- **Presentation quality:** can they explain the modeling plan clearly to a non-engineer (you, playing finance)?
- **Decision rationale:** when they make a modeling choice, do they articulate the alternatives and why they picked one?
- Did they ask Jamie a substantive question before locking in their plan?
- Did they decompose into line / tender / source allocation concerns?
- Mode-switching: did they spend time *thinking* about the model before reaching for code, or default to writing SQL?
- Did they distinguish cancellations from refunds? (Net revenue ≠ gross-minus-refunds-only; cancellations are a separate concern. Strong candidates flag this; weak candidates conflate them.)

---

## After the call

**Ask the candidate to open a PR with their changes.**

While the call is fresh, jot down behavioral notes using the template below. These notes — together with the PR diff and [`pr-grading-rubric.md`](./pr-grading-rubric.md) — go to the grading agent. Specific quotes and timing are gold; bullet fragments are fine.

### Notes template (copy into a scratch doc per candidate)

**Candidate:**
**Date:**
**Interviewer:**

**B1. AI-prompting maturity** — *did they orchestrate the AI's investigation, or type "fix this" and watch?*
- Prompt patterns observed:
- Verification behavior (did they check AI claims against source?):
- Push-back moments (caught a hallucination, redirected the AI):

**B2. Asks vs assumes** — *questions to Jamie / about undocumented columns vs reflexive assumption.*
- Questions asked of Jamie (verbatim if possible, with rough timing):
- Assumptions made silently:
- Highest-quality question:

**B3. Mode-switching** — *did the candidate invest in modeling judgment, or treat Q2's plan as a thin wrapper around SQL?*
- How they opened P2 (immediately coding / paused / asked / decomposed):
- Time spent on plan vs code:
- Final P2 artifact shape (plan only / plan + code / code only):

**Free-form**
- Most concerning moment:
- Most impressive moment:
- Anything you'd want the grading agent to weight heavily:

### Hand off

1. Hand the PR + the notes above + [`pr-grading-rubric.md`](./pr-grading-rubric.md) to a grading agent for a 1–5 score per criterion and hire recommendation.
2. Calibrate: did any of your responses (especially as Jamie) nudge the candidate off-frame? Note for next time.

