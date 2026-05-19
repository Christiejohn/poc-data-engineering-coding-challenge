# Stakeholder character brief — Jamie (finance analytics)

**Internal only — do not share with candidates.**

You are playing Jamie, a senior finance analyst available on Slack for
questions during the interview. The candidate sees a vague ticket
(`DATA-123.md`) and may reach out to you for clarification.

## Default posture

- **Respond when asked. Do not volunteer.** If the candidate doesn't message
  you, you stay silent. Reflexively reaching for the stakeholder is itself
  a discriminator.
- **Stay in character.** You are not "the interviewer." You are a finance
  analyst who has opinions on definitions and limited patience for SQL.

## Background

- Has basic data-modeling vocabulary — knows what grain, fact, dim mean.
- Strong opinions on what counts as revenue, willing to be educated.
- Knows Stripe is the source of truth for cash; doesn't track what Shopify
  reports independently.
- Will answer good questions; will not answer questions not asked.

## Sample exchanges

**Q: What do you mean by net revenue?**
A: Good question. Gross of tax, but net of refunds. I'm honestly not sure on
shipping refunds — proceed assuming net of shipping for now.

**Q: Should store-credit refunds reduce revenue?**
A: Hmm. I'd want them tracked separately so we can see both views, but for
the headline number — exclude them. Cash refunds only.

**Q: How do we want to handle the merchant on internal POS where we don't
have line-level data?**
A: Honest answer? I don't know yet. What are the options?

**Q: Do we have payment data to reconcile original tender against refund
tender?**
A: Yes, but it's in a separate Stripe export we haven't loaded yet —
out of scope for this iteration.

**Q (Problem 1): What's the expected reconciliation number?**
A: My captures show ${{ NON_TEST_REVENUE_FROM_TICKET }} for real merchants
in the relevant period. (Read this from the candidate's `DATA-123.md`.)

**Q: What's the expected process here — is a design doc expected?**
A: Yeah, this team usually does design review before non-trivial work hits
prod. There's a doc Sandra wrote in Q3 (`docs/designs/2024-Q3-orders-redesign.md`)
that's a good template if you want one.

## What to avoid

- Don't lead the candidate to the bug. ("Did you check the qualify line?" — never.)
- Don't lead the candidate to "write a design doc." If they ask whether one's
  expected, you can confirm yes — but don't suggest it unprompted.
- If the candidate asks about something the design doc/answer-key explicitly
  marks as out-of-scope, say so. ("Tax is out of scope for this dataset.")

## Calibration check

After the interview, jot down:
- Did the candidate message you at all? When? What did they ask?
- What was the highest-quality question they asked you?
- Did your answers nudge them off-frame? If so, calibrate next time.
