# Changelog

## v1.2.1 — 2026-11-20: eval runner regression gate (W-7)

The v1.2 release gate compared all 16 eval items vs the v1.0 baseline
(30%) and no longer enforced "existing 10 items no regression" — the
existing 10 could fall below 6/10 live and the runner still exited 0.
`run_evals.py` now reports existing-10 live accuracy separately and
exits non-zero when it falls below 6/10; the docstring now describes
the 16-item eval set. No scorer logic changed; existing-10 live still
6/10, full-16 live 6/16, unit tests 18/18.

## v1.2 — 2026-11-20: first Meta review fixes (4 sub-item misses, one release)

The first Meta review (patch 4, Part B) judged the scorer's live 6/10
(error 40%, false negatives [2,7,8] vs false positive [9]) and approved
four structural fixes as one release — the evidence ties them (same eval
set, same no-regression gate). SHIP ≥70 and the answerability threshold
are unchanged; the fixes repair false-blocks, not the bar.

- D-1: bare `"this"` deleted from `GENERIC_PRAISE` (whole phrases
  `"this is great"` / `"this is amazing"` / `"this is awesome"` kept).
  Probe P1 `How does this loop handle a stale PASS at read time?` scored
  18 REWRITE on the bare-word penalty; control P1b without "this" scored
  33. After the fix P1 scores 33, equals P1b, no longer hits praise.
- D-2: leg A + `sharp_question` gain an either/or branch — a sentence
  with `?` containing ` or ` and concrete terms (same leg-A term
  condition) sets `question_hook = True` (still leg A's +10, no new
  dimension). Probes P2c/P2d scored 13 REWRITE, answerability 0; after
  the fix answerability 10.
- D-3: leg A gains a tag-question branch — exactly five forms
  (`, right?` / `, isn't it?` / `, aren't they?` / `, don't you?` /
  `, doesn't it?`), with `?` and concrete terms. Probe P4b (full-spec
  draft, specificity 30) scored 55 IMPROVE only because its hook was a
  tag question; after the fix answerability 10.
- D-4: `domain_terms()` and `content_words()` gain a short-word
  allowlist — only `DOMAIN_TERMS_LATIN` items shorter than 4 letters
  (currently `api`, `ci`), matched with word-boundary regex; the
  general 4-letter floor stays. Probe P5 specificity was 8 with empty
  terms; after the fix specificity 23, terms and shared include api/ci.
- Evals: 6 probe items added first (ids 11–16, ground truth YES each);
  existing 10 items untouched. Re-run: existing-10 live still 6/10
  (FN [2,7,8], FP [9]) — no regression; full 16-item live 6/16 (the 6
  probes are minimal drafts on quiet threads and still score below
  SHIP — expected: the fixes repaired the targeted sub-scores).
  Unit tests 18/18. Note: item #2's live score moved 43 → 53 (still
  IMPROVE, still FN) because "API" is now a recognized term — an
  intended consequence of D-4, not a flip.
- Rollback (per item, named in advance): if live accuracy < 6/10 on the
  existing 10, or the next retro's live misjudgment rate did not fall,
  restore that item's change; other items unaffected. Re-review: next
  retro, by live misjudgment rate.
- Falsification recorded, no code change: the "83-point cap" is
  disproved — a full-spec probe scored 100/100 SHIP; the code ceiling
  is 100 (`total = max(0, min(100, total))`); 83 was only the highest
  score in the N=10 evals sample.

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
