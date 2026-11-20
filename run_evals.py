#!/usr/bin/env python3
"""Re-run the reply-scorer eval set and report accuracy.

The eval set (evals.jsonl) is 16 items: 10 real replies from 2026-11-17
(ids 1–10, the original set, with corrected ground truth — did the
author reply back? — and the thread state at posting time) + 6 v1.2
probe drafts (ids 11–16, ground truth YES each, from the first Meta
review probes P1/P1b/P2c/P2d/P4b/P5). Prediction rule: SHIP (>= 70) =
the author will reply.

Two modes, printed side by side:
  plain  — score(draft) only: the original eval conditions (no --post,
           no --thread). Measures the draft-only dimensions.
  live   — score(draft, post, thread): how the scorer is actually used
           in a run, with the reconstructed one-line parent-post
           background and the thread prior.

Exit code: 0 = no regression vs the recorded baseline (v1.0: 3/10) AND
existing-10 live accuracy still >= 6/10; 1 = live-mode accuracy fell
below baseline, existing-10 live fell below 6/10, or the eval file is
broken. A fix that does not improve the numbers is still shippable if the
residuals are recorded — but a fix that REGRESSES is not.

Usage:
    python3 run_evals.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reply_scorer import score  # noqa: E402


def load(path):
    meta = None
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "meta" in obj:
                meta = obj["meta"]
            else:
                items.append(obj)
    return meta, items


def predict(result):
    return result["verdict"] == "SHIP"


def run_mode(items, use_context):
    rows = []
    correct = 0
    for it in items:
        if use_context:
            try:
                result = score(it["draft"], it["post"], it["thread"])
            except TypeError:
                # scorer predates the thread prior: fall back to post only
                result = score(it["draft"], it["post"])
        else:
            result = score(it["draft"])
        pred = predict(result)
        ok = pred == it["author_replied"]
        correct += ok
        rows.append({
            "id": it["id"],
            "score": result["score"],
            "verdict": result["verdict"],
            "prior_score": it["prior_score"],
            "pred": pred,
            "truth": it["author_replied"],
            "ok": ok,
        })
    return rows, correct


def report(name, rows, correct, total):
    print(f"--- {name} ---")
    print(f"{'id':>2} {'score':>5} {'was':>4} {'verdict':<8} {'pred':>5} {'truth':>5}  ok")
    for r in rows:
        print(f"{r['id']:>2} {r['score']:>5} {r['prior_score']:>4} "
              f"{r['verdict']:<8} {str(r['pred']):>5} {str(r['truth']):>5}  "
              f"{'✓' if r['ok'] else '✗'}")
    fn = [r["id"] for r in rows if r["truth"] and not r["pred"]]
    fp = [r["id"] for r in rows if r["pred"] and not r["truth"]]
    print(f"correct {correct}/{total}  error {(total - correct) / total:.0%}  "
          f"false negatives {fn or 'none'}  false positives {fp or 'none'}")
    print()
    return correct


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    meta, items = load(os.path.join(here, "evals.jsonl"))
    total = len(items)
    if total == 0:
        print("error: evals.jsonl has no items", file=sys.stderr)
        return 1

    plain_rows, plain_correct = run_mode(items, use_context=False)
    live_rows, live_correct = run_mode(items, use_context=True)
    report("plain (no post, no thread — original eval conditions)",
           plain_rows, plain_correct, total)
    report("live (with post + thread prior — how runs actually use it)",
           live_rows, live_correct, total)

    # Release gate (W-7, 2026-11-20): the existing-10 original items are
    # the no-regression set. The v1.0 baseline check below compares ALL
    # items, so a fall in the existing 10 alone would not trip it once
    # the probe items are in the file — this gate enforces it directly.
    existing_rows = [r for r in live_rows if r["id"] <= 10]
    existing_correct = sum(1 for r in existing_rows if r["ok"])
    print(f"existing-10 live: {existing_correct}/10")
    if existing_correct < 6:
        print("REGRESSION: existing-10 live accuracy is below 6/10 — "
              "do not ship this version.", file=sys.stderr)
        return 1

    baseline = meta.get("baseline_accuracy") if meta else None
    if baseline is not None:
        live_acc = live_correct / total
        print(f"baseline v1.0 accuracy: {baseline:.0%}  "
              f"live now: {live_acc:.0%}")
        if live_acc < baseline:
            print("REGRESSION: live accuracy is below the recorded "
                  "baseline — do not ship this version.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
