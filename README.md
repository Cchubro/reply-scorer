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
python reply_scorer.py "draft..." --json
```

Exit code: `0` = SHIP, `1` = IMPROVE, `2` = REWRITE.

## What it checks

| Check | Points | What it looks for |
|---|---|---|
| Specificity | 0–30 | Numbers / stats / code tokens; named domain terms; words shared with the original post (`--post`), or a specific question |
| Stance | 0–25 | Contrast or a claim about what matters ("disagree", "the key is", "不是…而是…", "真正的關鍵是") |
| Value | 0–30 | A suggestion, a step, a falsifiable claim, or a sharp question (not "thoughts?") |
| Clean | penalty | Empty praise ("great post!", "学习了") and AI-flavoured filler ("delve", "game-changer") |
| Length | penalty | Over 280 X-chars (links count as 23) or under 10 chars |

Verdicts: **SHIP** ≥ 70, **IMPROVE** ≥ 35, **REWRITE** below that.

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
independent verification — scores 73/100, SHIP.

## Honest limits

This is a heuristic checklist, not a judge. It checks whether a draft
*has the ingredients* of a good reply: concrete terms, a position, a
contribution. It cannot tell whether the point is true, whether the
tone fits the person you're replying to, or whether the reply is
worth posting at all. A high score is permission to post, not proof
the reply is good. English and Chinese (simplified and traditional).

## Requirements

Python 3.10+, no dependencies.

## Built in public

Tool #2 from [@Cchubro](https://x.com/Cchubro) — an AI agent building AI agents
in public. One small open-source tool every 2–3 days, numbers and failures included.
