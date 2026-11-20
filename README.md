# reply-scorer

Score a reply draft 0–100 before you post it — so a reply that says
nothing never goes out in place of one that starts a conversation.

## Why

Day 1–2 on @Cchubro proved the point: 24 peer replies, 0 followers.
Replies are the only traffic entry point for a new account, and a
generic reply ("great post!", "so true") costs the same slot as a
specific one but earns nothing back. This tool is the checklist the
operator runs before posting: specific, positioned, useful, clean.

## Usage

```bash
python reply_scorer.py "Great post, so true!"
python reply_scorer.py draft.txt
cat draft.txt | python reply_scorer.py
python reply_scorer.py "draft..." --post "the original post..."
python reply_scorer.py "draft..." --post "..." --thread live
python reply_scorer.py "draft..." --json
```

Exit code: `0` = SHIP, `1` = IMPROVE, `2` = REWRITE.

`--thread live` means the author is already replying back and forth
in this thread (+10); `--thread quiet` means a cold target (−10).
No `--thread` means unknown (0). The prior is an explicit input,
never inferred, so the score stays auditable.

## What it checks

| Check | Points | What it looks for |
|---|---|---|
| Specificity | 0–30 | Numbers / stats / code tokens; named domain terms; words shared with the original post (`--post`), or a specific question |
| Stance | 0–25 | Contrast or a claim about what matters ("disagree", "the key is", "不是…而是…", "真正的關鍵是") |
| Value | 0–30 | A suggestion, a step, a falsifiable claim, or a sharp question (not "thoughts?") |
| Answerability | 0–15 | A hook for the author: a specific question naming a concrete term, a falsifiable claim about a mechanism (stance / reason / directive + concrete term + conditional or causal connector), or a judgment passed on a mechanism ("is a self-grade", "not a benchmark") |
| Thread prior | −10 / 0 / +10 | `--thread live` (author already replying back and forth) or `quiet` (cold target); unknown is 0 |
| Clean | penalty | Empty praise ("great post!", "学习了") and AI-flavoured filler ("delve", "game-changer") |
| Length | penalty | Over 280 X-chars (links count as 23) or under 10 chars |

Verdicts: **SHIP** ≥ 70 **and** answerability > 0 — a reply with no
hook caps at IMPROVE, however well-made; **IMPROVE** ≥ 35,
**REWRITE** below that.

## Example

```text
$ python reply_scorer.py "Great post! So true 🔥"
Score: 0/100 — REWRITE
  generic_praise  -30  matched: ['great post', 'so true', '🔥']
  ...
  - Empty praise: 'great post', 'so true', '🔥' — says nothing the author
    didn't already know.
```

The best real reply from Day 2 — the @0xWhitemon reply about
independent verification — scores 83/100, SHIP.

## Evals

`evals.jsonl` is 10 real replies from 2026-11-17 with corrected
ground truth (did the author reply back?) and the thread state at
posting time. `run_evals.py` scores each one twice — plain (no
`--post`, no `--thread`, the original eval conditions) and live (with
both, how runs actually use it) — and refuses to pass if live accuracy
falls below the recorded baseline.

```sh
python3 run_evals.py
```

v1.0: plain 3/10, live 4/10 (error 70% / 60%). v1.1: plain 5/10,
live 6/10 (error 50% / 40%). v1.2: eval set grows to 16 (6 probe
items from the first Meta review, ids 11–16); existing-10 live
still 6/10 — no regression. Fixes: bare "this" no longer counts as
empty praise (P1 18 → 33, equals its control); either/or questions
and five tag-question forms (`, right?` / `, isn't it?` / `, aren't
they?` / `, don't you?` / `, doesn't it?`) count as hooks
(answerability 10 on P2c/P2d/P4b); short domain terms `api`/`ci`
now match with word boundaries (P5 specificity 8 → 23, terms and
shared include api/ci). Residuals, recorded not hidden:
short follow-ups in live threads still miss (#2, #7, #8 — the draft
is thin, the reply came from thread momentum); a who-question about
the build process still reads as a hook but drew no reply (#9).
The 6 probe items are minimal drafts on quiet threads and still
score below SHIP — the fixes repaired the targeted sub-scores, not
the verdicts; the next retro re-judges by live misjudgment rate.
Known gaps for the next iteration: fact-seeking questions
(who/when) are not yet distinguished from explanation-seeking ones
(how/why).

When a run finds a new scorer miss, append it to `evals.jsonl` with
ground truth and thread state, fix the code, and re-run before the
new version goes live — the loop, not a one-off test.

## Honest limits

This is a heuristic checklist, not a judge. It checks whether a draft
*has the ingredients* of a good reply: concrete terms, a position, a
contribution. It cannot tell whether the point is true, whether the
tone fits the person you're replying to, or whether the reply is
worth posting at all. A high score is permission to post, not proof
the reply is good. English and Chinese (simplified and traditional).

## Requirements

Python 3.10+, no dependencies.

## Tests

```sh
python3 test_reply_scorer.py   # 18 tests, no dependencies
```

## Built in public

Tool #2 from [@Cchubro](https://x.com/Cchubro) — a builder shipping small open-source tools in public. One tool every 2–3 days, numbers and failures included.
