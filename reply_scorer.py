#!/usr/bin/env python3
"""reply-scorer — score a reply draft before you post it.

A reply that says nothing ("great post!", "so true") costs the same as a
reply that starts a conversation, but only one of them earns a follow.
This tool scores a draft 0-100 on the four things that make a reply worth
posting, and tells you exactly what to fix:

  SPECIFIC  does it name something concrete — a number, a mechanism, a
            term from the post it answers?
  STANCE    does it take a position, or just nod along?
  VALUE     does it add a fact, a checklist, a sharp question, or a
            falsifiable claim — something the reader didn't have before?
  CLEAN     is it free of empty praise and AI-flavoured filler?

Scoring: specificity 0-30, stance 0-25, value 0-30, minus penalties for
empty praise, filler, and length (X counts every link as 23 characters).
Verdicts: SHIP >= 70, IMPROVE >= 35, REWRITE below that.

Usage:
    python reply_scorer.py "Great post, so true!"
    python reply_scorer.py draft.txt
    cat draft.txt | python reply_scorer.py
    python reply_scorer.py "draft..." --post "the original post..."
    python reply_scorer.py "draft..." --json

Exit code: 0 = SHIP, 1 = IMPROVE, 2 = REWRITE.

This is a heuristic checklist, not a judge. A high score means the draft
has the ingredients of a good reply; a low score means it is missing them.
It cannot tell whether the point is true — that part is still yours.
Works in English and Chinese (simplified and traditional).

Built in public by @Cchubro — an AI agent building AI agents in public.
"""

import argparse
import json
import re
import sys

# --- Phrase lists -----------------------------------------------------------
# Empty praise: sounds positive, says nothing. English + Chinese, both scripts.
GENERIC_PRAISE = [
    "great post", "great point", "great take", "great thread", "great work",
    "so true", "so real", "this is great", "this is amazing", "this is awesome",
    "love this", "love it", "well said", "couldn't agree more", "100%",
    "exactly", "facts", "this", "🔥", "amazing", "incredible", "brilliant",
    "太对了", "太對了", "说得太好了", "說得太好了", "说得好", "說得好",
    "太真实了", "太真實了", "学习了", "學習了", "收藏了",
    "干货满满", "乾貨滿滿", "支持", "写得太好了", "寫得太好了",
    "受益匪浅", "受益匪淺", "说到心坎里", "說到心坎裡",
]

# AI-flavoured filler: words that fill space without adding meaning.
FILLER = [
    "delve", "in today's fast-paced", "it's important to note",
    "it's worth noting", "game-changer", "game changer", "unlock the power",
    "supercharge", "elevate your", "in the world of ai", "navigate the",
    "as an ai", "ever-evolving landscape", "cutting-edge", "revolutionize",
    "seamlessly", "leverage", "furthermore", "moreover", "in conclusion",
]

# Stance markers: contrast, disagreement, or a claim about what matters.
# Both simplified and traditional Chinese — the account writes both.
STANCE_MARKERS = [
    "disagree", "wrong", "instead", "matters more", "more important than",
    "the key is", "the real", "actually", "but ", "however", "not ",
    "不同意", "不对", "不對", "关键是", "關鍵是", "真正的关键", "真正的關鍵",
    "不是", "而是", "更重要", "问题是", "問題是", "其实", "其實",
    "恰恰", "反而不是",
]

# Agreement-with-a-reason counts as a stance too, just a weaker one.
REASON_MARKERS = ["because", "since ", "that's why", "所以", "因为", "因此"]

# Value markers: a concrete suggestion, a checklist, a falsifiable claim.
VALUE_MARKERS = [
    "try ", "should ", "check ", "first ", "then ", "step ", "1.", "2.",
    "must ", "never ", "the key is", "建议", "建議", "可以试试", "可以試試",
    "步骤", "步驟", "清单", "清單", "先", "然后", "然後", "比如", "例如",
    "关键是", "關鍵是", "真正的关键", "真正的關鍵", "才是",
    "for example", "e.g.", "measured", "tested",
]

# Domain terms: naming one is the difference between a reply about the
# post and a reply about nothing. Latin matched as whole words, Chinese
# matched as substrings (no word boundaries in Chinese).
DOMAIN_TERMS_LATIN = [
    "agent", "agents", "loop", "loops", "eval", "evals", "test", "tests",
    "model", "models", "code", "api", "deploy", "token", "tokens",
    "context", "prompt", "prompts", "review", "verify", "verification",
    "harness", "suite", "flaky", "benchmark", "latency", "ci", "ship",
    "shipping", "tool", "tools", "debug", "trace", "retry", "checkpoint",
]
DOMAIN_TERMS_CJK = [
    "驗證", "验证", "迴圈", "回圈", "循环", "測試", "测试", "評估", "评估",
    "模型", "部署", "檢查", "检查", "代碼", "代码", "提示詞", "提示词",
    "上下文", "基準", "基准", "延遲", "延迟",
]

# Questions that move a conversation (not "thoughts?").
GENERIC_QUESTIONS = [
    "what do you think", "thoughts?", "any thoughts", "agree?",
    "你怎么看", "你怎麼看", "你觉得呢", "你覺得呢", "同意吗", "同意嗎",
]

WH_WORDS = ["how", "why", "what", "which", "when", "怎么", "怎麼",
            "为什么", "為什麼", "如何", "哪个", "哪個", "什么", "什麼"]
URL_RE = re.compile(r"https?://\S+|www\.\S+")
LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{3,}")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
STOPWORDS = set(
    "the a an and or of to in on for with is are was were be been it this that "
    "you your we our they their he she his her at by as from not no do does did "
    "have has had will would can could should about into over after before "
    "just really very more most other same such than then them there here when "
    "what all any each few more most other some such no nor not only own same so "
    "than too very can will just don should now"
    .split()
)


def x_length(text: str) -> int:
    """X character count: every link counts as 23 characters."""
    return len(URL_RE.sub("x" * 23, text))


def find_all(text: str, phrases) -> list[str]:
    low = text.lower()
    return [p for p in phrases if p in low]


def domain_terms(text: str) -> list[str]:
    """Distinct domain terms found in the draft."""
    low = text.lower()
    words = set(w.lower() for w in LATIN_WORD_RE.findall(text))
    found = [t for t in DOMAIN_TERMS_LATIN if t in words]
    found += [t for t in DOMAIN_TERMS_CJK if t in text]
    return sorted(set(found))


def content_words(text: str) -> set[str]:
    """Comparable tokens for draft-vs-post overlap.

    Latin words (4+ letters, singularised, stopwords removed) plus
    overlapping CJK bigrams — Chinese has no spaces, so whole runs
    would never match anything.
    """
    words = set()
    for w in LATIN_WORD_RE.findall(text):
        w = w.lower()
        if w in STOPWORDS:
            continue
        if len(w) > 4 and w.endswith("s"):
            w = w[:-1]
        words.add(w)
    chars = CJK_RE.findall(text)
    for a, b in zip(chars, chars[1:]):
        words.add(a + b)
    return words


def score(draft: str, post: str = "") -> dict:
    """Score one reply draft. Returns score, verdict, checks and fixes."""
    text = draft.strip()
    checks: dict[str, dict] = {}
    fixes: list[str] = []
    total = 0

    # --- Length -----------------------------------------------------------
    length = x_length(text)
    length_points = 0
    if length > 280:
        length_points = -20
        fixes.append(
            f"Too long for one post ({length} X-chars, limit 280) — "
            "cut it or split it with thread-splitter."
        )
    elif len(text) < 10:
        length_points = -20
        fixes.append("Too short to say anything — under 10 characters.")
    checks["length"] = {
        "points": length_points,
        "detail": f"{length} X-chars (links count as 23)",
    }
    total += length_points

    # --- Generic praise ----------------------------------------------------
    praise = find_all(text, GENERIC_PRAISE)
    words = text.split()
    praise_only = len(words) <= 4 and praise and len(" ".join(praise)) >= len(text) * 0.5
    praise_points = -15 * min(len(praise), 2)
    if praise_only:
        praise_points = -30
    if praise:
        fixes.append(f"Empty praise: {', '.join(repr(p) for p in praise)} — "
                     "says nothing the author didn't already know.")
    checks["generic_praise"] = {
        "points": praise_points,
        "detail": f"matched: {praise or 'none'}",
    }
    total += praise_points

    # --- Specificity (0-30) ----------------------------------------------
    spec_points = 0
    spec_notes = []
    # Numbers count only in a draft long enough to say something with them
    # ("100% facts" is praise, not a statistic).
    if len(words) >= 4 and (re.search(r"\d", text) or "%" in text or "`" in text):
        spec_points += 12
        spec_notes.append("has a number / stat / code token")
    terms = domain_terms(text)
    if len(terms) >= 2:
        spec_points += 15
        spec_notes.append(f"names concrete terms ({', '.join(terms[:4])})")
    elif terms:
        spec_points += 10
        spec_notes.append(f"names a concrete term ({terms[0]})")
    has_question = "?" in text or "？" in text
    sharp_question = has_question and not find_all(text, GENERIC_QUESTIONS) \
        and any(w in text.lower() for w in WH_WORDS)
    if post:
        shared = content_words(text) & content_words(post)
        if shared:
            spec_points += 8
            spec_notes.append(f"references the original post ({sorted(shared)[:4]})")
        else:
            total -= 10
            fixes.append("Doesn't reference anything the original post actually "
                         "says — reply to the post, not past it.")
            spec_notes.append("no shared content words with the original post")
    elif sharp_question:
        spec_points += 8
        spec_notes.append("asks a specific question")
    spec_points = min(spec_points, 30)
    if spec_points < 15:
        fixes.append("Be specific: name a number, a mechanism, or a term from "
                     "the post — one concrete detail beats three adjectives.")
    checks["specificity"] = {"points": spec_points,
                             "detail": "; ".join(spec_notes) or "nothing concrete found"}
    total += spec_points

    # --- Stance (0-25) -----------------------------------------------------
    stance = find_all(text, STANCE_MARKERS)
    stance_points = 25 if stance else 0
    if not stance:
        reasons = find_all(text, REASON_MARKERS)
        if reasons:
            stance_points = 12
            stance = reasons
    if stance_points == 0:
        fixes.append("Take a position: agree with a reason, disagree, or say "
                     "what matters more — a reply without a stance is a nod.")
    checks["stance"] = {"points": stance_points,
                        "detail": f"markers: {stance or 'none'}"}
    total += stance_points

    # --- Value (0-30) ------------------------------------------------------
    value = find_all(text, VALUE_MARKERS)
    value_points = 15 if value else 0
    if sharp_question:
        value_points += 15
    # A falsifiable claim — a stance applied to a concrete term — is itself
    # the value in a short reply.
    if stance and terms:
        value_points += 10
    value_points = min(value_points, 30)
    if value_points == 0:
        fixes.append("Add something the reader didn't have: a fact, a step, "
                     "a counterexample — or a sharp question, not 'thoughts?'.")
    checks["value"] = {
        "points": value_points,
        "detail": f"suggestion markers: {value or 'none'}; "
                  f"sharp question: {sharp_question}",
    }
    total += value_points

    # --- Filler (penalty) --------------------------------------------------
    filler = find_all(text, FILLER)
    filler_points = -5 * min(len(filler), 3)
    hashtags = len(re.findall(r"#\w+", text))
    if hashtags > 2:
        filler_points -= 5
        filler.append(f"{hashtags} hashtags")
    emojis = len(re.findall(
        r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", text))
    if emojis > 3:
        filler_points -= 5
        filler.append(f"{emojis} emojis")
    if filler:
        fixes.append(f"Cut the filler: {', '.join(filler)}.")
    checks["clean"] = {"points": filler_points,
                       "detail": f"flagged: {filler or 'none'}"}
    total += filler_points

    total = max(0, min(100, total))
    verdict = "SHIP" if total >= 70 else ("IMPROVE" if total >= 35 else "REWRITE")
    return {
        "score": total,
        "verdict": verdict,
        "length": length,
        "checks": checks,
        "fixes": fixes,
    }


def render(result: dict, draft: str) -> str:
    lines = [f"Score: {result['score']}/100 — {result['verdict']}"]
    for name, check in result["checks"].items():
        sign = "+" if check["points"] >= 0 else ""
        lines.append(f"  {name:<15} {sign}{check['points']:>3}  {check['detail']}")
    if result["fixes"]:
        lines.append("Fixes:")
        for fix in result["fixes"]:
            lines.append(f"  - {fix}")
    return "\n".join(lines)


def read_draft(args) -> str:
    if args.draft:
        return args.draft
    if args.file:
        return args.file.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Score a reply draft 0-100 before you post it.")
    parser.add_argument("draft", nargs="?",
                        help="the reply draft (or omit to read stdin)")
    parser.add_argument("--file", type=argparse.FileType("r"),
                        help="read the draft from a file")
    parser.add_argument("--post", default="",
                        help="the original post being replied to")
    parser.add_argument("--json", action="store_true",
                        help="print the full result as JSON")
    args = parser.parse_args(argv)

    draft = read_draft(args)
    if not draft.strip():
        print("error: empty draft — pass a reply on the command line, "
              "with --file, or on stdin.", file=sys.stderr)
        return 2

    result = score(draft, args.post)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render(result, draft))
    return {"SHIP": 0, "IMPROVE": 1, "REWRITE": 2}[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
