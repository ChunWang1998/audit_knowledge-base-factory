#!/usr/bin/env python3
"""Prepare SkillOpt train/val splits from knowledgeBase/**/issues.json.

Walks the hierarchical knowledge base, groups issues by top-level category,
shuffles with a fixed seed, splits 50/50 per category, and writes SkillOpt
items to skillopt/data/audit/{category}/{train,val}/items.json.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

CATEGORY_SLUGS: dict[str, str] = {
    "Accounting": "accounting",
    "Access Control": "access-control",
    "Griefing Attacks": "griefing-attacks",
    "DoS / Liveness": "dos-liveness",
    "Token Transfer": "token-transfer",
    "Upgrade / Config": "upgrade-config",
    "External Dependencies": "external-dependencies",
}

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KB_ROOT = REPO_ROOT / "knowledgeBase"
DEFAULT_OUT_ROOT = REPO_ROOT / "skillopt" / "data" / "audit"


def _format_functions(functions: Any) -> str:
    if not functions:
        return "N/A"
    if isinstance(functions, list):
        return ", ".join(str(fn) for fn in functions)
    return str(functions)


def _taxonomy_path(kb_root: Path, issues_path: Path) -> str:
    rel = issues_path.parent.relative_to(kb_root)
    return "/".join(rel.parts)


def _build_question(issue: dict[str, Any]) -> str:
    code = (issue.get("code_snippet") or "").strip()
    contract = issue.get("contract_name") or "Unknown"
    functions = _format_functions(issue.get("functions_affected"))
    return (
        "Audit this Solidity code:\n"
        f"```solidity\n{code}\n```\n"
        f"Contract: {contract}\n"
        f"Functions: {functions}"
    )


def _to_item(issue: dict[str, Any], category_slug: str, taxonomy_path: str) -> dict[str, Any]:
    tags = issue.get("tags") or []
    if not tags:
        raise ValueError(f"Issue {issue.get('id')} has no tags")

    return {
        "id": issue["id"],
        "question": _build_question(issue),
        "context": issue.get("description") or "",
        "answers": [str(tag) for tag in tags],
        "category": category_slug,
        "taxonomy_path": taxonomy_path,
        "severity": issue.get("severity"),
        "source": issue.get("source"),
        "location": issue.get("location"),
    }


def _load_issues(kb_root: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for issues_path in sorted(kb_root.rglob("issues.json")):
        raw = json.loads(issues_path.read_text())
        issues = raw if isinstance(raw, list) else raw.get("issues", [])
        taxonomy_path = _taxonomy_path(kb_root, issues_path)

        for issue in issues:
            category = issue.get("category")
            if category not in CATEGORY_SLUGS:
                raise KeyError(
                    f"Unknown category {category!r} in {issues_path}. "
                    f"Expected one of {sorted(CATEGORY_SLUGS)}"
                )

            code = (issue.get("code_snippet") or "").strip()
            if not code:
                continue

            category_slug = CATEGORY_SLUGS[category]
            grouped[category_slug].append(
                _to_item(issue, category_slug, taxonomy_path)
            )

    return grouped


def _split_items(items: list[dict[str, Any]], seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(items)
    rng.shuffle(shuffled)
    mid = len(shuffled) // 2
    if mid == 0:
        return shuffled, []
    return shuffled[:mid], shuffled[mid:]


def _write_split(out_dir: Path, name: str, items: list[dict[str, Any]]) -> None:
    split_dir = out_dir / name
    split_dir.mkdir(parents=True, exist_ok=True)
    (split_dir / "items.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n"
    )


def prepare_dataset(
    kb_root: Path,
    out_root: Path,
    seed: int = 42,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    grouped = _load_issues(kb_root)
    manifest: dict[str, Any] = {
        "kb_root": str(kb_root),
        "out_root": str(out_root),
        "seed": seed,
        "categories": {},
        "total_issues": 0,
    }

    selected = sorted(grouped)
    if categories:
        unknown = sorted(set(categories) - set(grouped))
        if unknown:
            raise ValueError(f"Requested categories not found in knowledge base: {unknown}")
        selected = categories

    for category_slug in selected:
        items = grouped[category_slug]
        train_items, val_items = _split_items(items, seed)
        category_dir = out_root / category_slug
        _write_split(category_dir, "train", train_items)
        _write_split(category_dir, "val", val_items)

        manifest["categories"][category_slug] = {
            "total": len(items),
            "train": len(train_items),
            "val": len(val_items),
        }
        manifest["total_issues"] += len(items)

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SkillOpt audit dataset splits")
    parser.add_argument(
        "--kb-root",
        type=Path,
        default=DEFAULT_KB_ROOT,
        help=f"Path to knowledgeBase/ (default: {DEFAULT_KB_ROOT})",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=DEFAULT_OUT_ROOT,
        help=f"Output root for audit splits (default: {DEFAULT_OUT_ROOT})",
    )
    parser.add_argument("--seed", type=int, default=42, help="Shuffle seed for 50/50 split")
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="Only prepare one or more category slugs (repeatable)",
    )
    args = parser.parse_args()

    manifest = prepare_dataset(
        kb_root=args.kb_root.resolve(),
        out_root=args.out_root.resolve(),
        seed=args.seed,
        categories=args.categories,
    )

    print(f"Prepared {manifest['total_issues']} issues into {args.out_root}")
    for slug, counts in manifest["categories"].items():
        print(
            f"  {slug}: total={counts['total']} "
            f"train={counts['train']} val={counts['val']}"
        )
    print(f"Manifest: {args.out_root / 'manifest.json'}")


if __name__ == "__main__":
    main()
