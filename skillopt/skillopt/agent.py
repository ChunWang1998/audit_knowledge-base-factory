"""凍結的智能合約安全審計 agent。

此 agent 不會被訓練。唯一可調整的輸入是技能文字（audit checklist），
注入到 system prompt。給定一個含漏洞的 Solidity code snippet，它會輸出
漏洞類型（Vulnerability Type）、分類路徑（Category），及簡短說明。
評分器（evaluator）隨後比對預測文字中是否出現預期的 tags。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from .config import Config
from .llm import ChatLLM

BASE_INSTRUCTIONS = (
    "You are a smart contract security auditor.\n"
    "Below is your audit skill (checklist). Apply it strictly.\n\n"
    "# Skill\n"
    "{skill}"
)

USER_TEMPLATE = (
    "{question}\n\n"
    "Respond with:\n"
    "- Vulnerability Type: (exact tag from taxonomy, e.g. hardcoded-overpayment)\n"
    "- Category: (taxonomy path, e.g. accounting/payout-errors/hardcoded-overpayment, ≥3 layers)\n"
    "- Explanation: (1-2 sentences)\n"
)


@dataclass
class Trajectory:
    item_id: str
    question: str
    gold: list[str]
    prediction: str
    raw_response: str
    correct: bool = False  # 由 evaluator 填入


def _parse_answer(raw: str) -> str:
    """保留完整回應，讓 tag recall 評分器做子字串比對。"""
    return raw.strip()


def run_one(llm: ChatLLM, cfg: Config, skill: str, item: dict[str, Any]) -> Trajectory:
    system = BASE_INSTRUCTIONS.format(skill=skill).strip()
    user = USER_TEMPLATE.format(question=item["question"])
    raw = llm.chat(
        system,
        user,
        model=cfg.model.target_model,
        temperature=cfg.model.temperature,
        max_tokens=cfg.model.max_tokens,
    )
    return Trajectory(
        item_id=item["id"],
        question=item["question"],
        gold=item["answers"],
        prediction=_parse_answer(raw),
        raw_response=raw,
    )


def run_batch(llm: ChatLLM, cfg: Config, skill: str,
              items: list[dict[str, Any]]) -> list[Trajectory]:
    """平行 rollout agent 跑過所有項目（API 呼叫是 IO-bound）。"""
    workers = max(1, cfg.train.workers)
    if workers == 1:
        return [run_one(llm, cfg, skill, it) for it in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda it: run_one(llm, cfg, skill, it), items))
