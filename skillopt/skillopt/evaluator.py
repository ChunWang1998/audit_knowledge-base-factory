"""SQuAD/HotpotQA 風格的答案評分(Exact Match 與 token F1)，
以及 audit 用途的 tag recall 評分。

正規化沿用官方 HotpotQA 評估:轉小寫、移除冠詞、去標點、收斂空白。
正規化後完全相符即把該軌跡標記為 `correct`。

audit 模式改用 tag recall:只要預測文字中出現任何一個預期 tag（詞邊界比對）
即視為命中，並將軌跡標記為 `correct`。
"""

from __future__ import annotations

import re
import string
from collections import Counter
from dataclasses import dataclass, field

from .agent import Trajectory

_ARTICLES = re.compile(r"\b(a|an|the)\b", re.UNICODE)
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(_PUNCT_TABLE)
    text = _ARTICLES.sub(" ", text)
    return " ".join(text.split())


def exact_match(pred: str, golds: list[str]) -> float:
    npred = normalize(pred)
    return float(any(npred == normalize(g) for g in golds))


def f1(pred: str, golds: list[str]) -> float:
    best = 0.0
    pred_toks = normalize(pred).split()
    for gold in golds:
        gold_toks = normalize(gold).split()
        if not pred_toks or not gold_toks:
            best = max(best, float(pred_toks == gold_toks))
            continue
        common = Counter(pred_toks) & Counter(gold_toks)
        same = sum(common.values())
        if same == 0:
            continue
        precision = same / len(pred_toks)
        recall_score = same / len(gold_toks)
        best = max(best, 2 * precision * recall_score / (precision + recall_score))
    return best


def tag_recall(predicted_text: str, tags: list[str]) -> float:
    """Return 1.0 if ANY expected tag appears as a standalone term in the prediction.

    Each tag is tested in two surface forms:
      - hyphenated original  (e.g. "hardcoded-overpayment")
      - space-normalised form (e.g. "hardcoded overpayment")
    so that model outputs in either style are accepted.

    Boundary rule: the match must NOT be immediately preceded or followed by a
    letter, digit, underscore, or hyphen. This avoids false positives where a
    short tag like "reentrancy" appears embedded inside "reentrancy-guard".
    (Standard \\b cannot block this because hyphen is itself a non-word char.)
    """
    _BOUNDARY = r"(?<![a-z0-9_-])", r"(?![a-z0-9_-])"
    pred = predicted_text.lower()
    for tag in tags:
        tag_lower = tag.lower()
        forms = {tag_lower, tag_lower.replace("-", " ")}
        for form in forms:
            pattern = _BOUNDARY[0] + re.escape(form) + _BOUNDARY[1]
            if re.search(pattern, pred):
                return 1.0
    return 0.0


@dataclass
class EvalResult:
    em: float
    f1: float
    n: int
    recall: float = field(default=0.0)

    def metric(self, name: str) -> float:
        return {"em": self.em, "f1": self.f1, "recall": self.recall}[name]


def evaluate(trajectories: list[Trajectory]) -> EvalResult:
    """Score in-place (sets .correct via EM) and aggregate EM, F1, recall."""
    if not trajectories:
        return EvalResult(em=0.0, f1=0.0, n=0, recall=0.0)
    em_sum = f1_sum = recall_sum = 0.0
    for t in trajectories:
        em = exact_match(t.prediction, t.gold)
        t.correct = em >= 1.0
        em_sum += em
        f1_sum += f1(t.prediction, t.gold)
        recall_sum += tag_recall(t.prediction, t.gold)
    n = len(trajectories)
    return EvalResult(em=em_sum / n, f1=f1_sum / n, n=n, recall=recall_sum / n)


def evaluate_recall(trajectories: list[Trajectory]) -> EvalResult:
    """Score in-place using tag recall as the primary correctness signal.

    Use this for audit tasks: t.correct is set to True whenever ANY expected
    tag is found in the prediction. The optimizer's failure analysis then
    focuses on missed vulnerability tags rather than exact-string matches.
    """
    if not trajectories:
        return EvalResult(em=0.0, f1=0.0, n=0, recall=0.0)
    em_sum = f1_sum = recall_sum = 0.0
    for t in trajectories:
        r = tag_recall(t.prediction, t.gold)
        t.correct = r >= 1.0
        em_sum += exact_match(t.prediction, t.gold)
        f1_sum += f1(t.prediction, t.gold)
        recall_sum += r
    n = len(trajectories)
    return EvalResult(em=em_sum / n, f1=f1_sum / n, n=n, recall=recall_sum / n)
