"""Lightweight lexical analysis for this engine's routing and intake matching.

Everywhere this kit previously matched a signal word against request text, it did so with a
plain substring check (`needle in haystack`). That has two concrete failure modes fixed here:

1. False positives across word boundaries - "test" matches inside "fastest" and "latest",
   "review" (in intake-request.py's old regex) matches inside "preview", because a substring
   check doesn't know where one word ends and another begins.
2. False negatives across word forms - a signal list author has to spell out "test", "tests",
   and "testing" separately to catch all three, or the match silently fails for whichever form
   they didn't think to add.

This module tokenizes text into words and applies a small suffix-stripping stemmer so matching
is word-aware and form-tolerant without pulling in an NLP dependency. It keeps the same scoring
weights the kit already used (phrase signals score higher than single-word signals) so existing
routing fixtures keep their expected outcome - the fix is removing false matches and loosening
word-form rigidity, not renumbering the scale.

It also adds what plain substring scoring never had: explicit tie detection. `top_candidates`
returns every candidate tied for the highest score instead of silently returning one winner, so
callers can treat a genuine tie as the ambiguity it is (this engine's own HITL case 2 - "two materially
correct answers and no governing requirement... selects between them") instead of masking it
with whichever candidate happened to be scored first.
"""
import re

# Suffixes stripped in this order, longest first, so a word is only reduced once. This is a
# small heuristic stemmer, not a linguistic one - it exists to fold "test/tests/testing/tested"
# and similar routine plural/tense variation onto one root, not to handle irregular English.
_SUFFIX_RULES = [
    ("ies", "y"),
    ("ing", ""),
    ("ers", "er"),
    ("ed", ""),
    ("es", ""),
    ("s", ""),
]
# Words short enough, or common enough, that suffix-stripping would create a false match
# ("as" -> "a", "is" -> "i", "ui" already ends its own way) rather than fold a real variant.
_STEM_EXCEPTIONS = {"as", "is", "gas", "bus", "status", "ui", "api", "os", "vs"}


def stem(word):
    word = word.lower()
    if word in _STEM_EXCEPTIONS or len(word) <= 3:
        return word
    for suffix, replacement in _SUFFIX_RULES:
        if suffix == "ed" and word.endswith("eed"):
            # Words like "seed"/"need"/"feed"/"speed" end in "ed" but the "ed" is part of the
            # root, not a past-tense inflection - stripping it would desync the base word from
            # its own "-ing" form ("seeding" strips to "seed" via the ing rule; "seed" must stem
            # to the same "seed", not get double-stripped down to "se").
            continue
        if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 2:
            return word[: -len(suffix)] + replacement
    return word


def tokenize(text):
    """Split into lowercase word tokens and stem each. Hyphens are treated as separators, not kept
    inside a token - "role-based" becomes ["role", "based"], matching the manifests' own mix of
    plain-word signals ("role") and hyphenated-phrase signals ("role-based") against the same
    text. Keeping hyphens joined would make a signal like "role" stop matching text that only
    contains "role-based", which is exactly the partial match the substring approach used to give
    for free."""
    words = re.findall(r"[a-z0-9]+", str(text or "").lower())
    return [stem(word) for word in words]


def _signal_tokens(signal):
    return tokenize(signal)


def phrase_present(text_tokens, signal_tokens):
    """True if signal_tokens appears as a contiguous, in-order run inside text_tokens."""
    if not signal_tokens:
        return False
    n = len(signal_tokens)
    return any(text_tokens[i : i + n] == signal_tokens for i in range(len(text_tokens) - n + 1))


def lexical_score(text, signals):
    """Word-aware replacement for the kit's old substring-based score_signals.

    Same weights as before (phrase signals score 3, single-word signals score 1) so existing
    routing fixtures keep their expected winner - what changes is *which* occurrences count:
    real word/phrase matches only, not incidental substrings that cross word boundaries.
    """
    text_tokens = tokenize(text)
    score = 0
    matched = []
    for signal in signals or []:
        signal_tokens = _signal_tokens(signal)
        if phrase_present(text_tokens, signal_tokens):
            score += 3 if len(signal_tokens) > 1 else 1
            matched.append(str(signal))
    return score, matched


def lexical_contains(text, phrase):
    """Word-aware replacement for `phrase in text.lower()` - used for simple inclusive OR checks
    (e.g. phased_triggers) that don't compete against alternatives and so don't need scoring."""
    return phrase_present(tokenize(text), _signal_tokens(phrase))


def top_candidates(scored):
    """Given [(label, score), ...], return (best_score, [labels tied for best_score]).

    Ties are only meaningful above zero - every candidate tied at score 0 just means nothing
    matched anything, not that two options are equally valid.
    """
    if not scored:
        return 0, []
    best = max(score for _, score in scored)
    if best <= 0:
        return best, []
    return best, [label for label, score in scored if score == best]
