# Changelog

## v1.1 — 2026-11-19: answerability + thread prior (evals-driven)

The 2026-11-19 evals (10 real replies from 2026-11-17, corrected
ground truth) showed the v1.0 scorer measured whether a reply is
well-made, not whether the author has anything to answer: five true
replies scored below SHIP while two SHIPs drew no reply.

- New dimension: **answerability (0–15)**. A hook is a specific
  question naming a concrete term, a falsifiable mechanism claim
  (stance / reason / directive + concrete term + conditional or
  causal connector), or a judgment passed on a mechanism
  ("is a self-grade", "not a benchmark", "is just decoration").
  The connectors are structural, not topic keywords — this is a new
  dimension, not a keyword-table tweak.
- New input: **`--thread live|quiet`** (thread prior −10 / 0 / +10).
  Live = author already replying back and forth; quiet = cold
  target. Explicit, never inferred.
- New gate: **SHIP requires answerability > 0**. A reply that scores
  ≥ 70 on craft but gives the author nothing to answer caps at
  IMPROVE.
- New files: `evals.jsonl` (the 10-item eval set, verbatim drafts,
  reconstructed one-line parent-post backgrounds, corrected ground
  truth, thread labels with rationale) and `run_evals.py` (plain +
  live runs, exits non-zero on regression below the v1.0 baseline).
- Evals: v1.0 plain 3/10, live 4/10. **v1.1 plain 5/10, live 6/10**
  (error 70% → 50% plain, 60% → 40% live). Unit tests 13 → 18.
- Residuals (recorded, not hidden): short follow-ups in live threads
  still miss (#2, #7, #8 — thin drafts, replies came from thread
  momentum); a who-question about the build process still reads as a
  hook but drew no reply (#9). Known gaps for the next iteration:
  3-letter domain terms (`api`, `ci`) never match the 4+-letter word
  regex; fact-seeking questions (who/when) not yet distinguished
  from explanation-seeking ones (how/why).

## v1.0 — 2026-11-10

First public version: specificity 0–30, stance 0–25, value 0–30,
penalties for empty praise, filler, and length. SHIP ≥ 70.
