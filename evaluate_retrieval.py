from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from rag_service import RagService


BASE_DIR = Path(__file__).resolve().parent
TEST_QUESTIONS_PATH = BASE_DIR / "knowledge_base" / "test_questions.json"
TEST_GROUPS = ("answerable", "must_escalate", "out_of_scope")


@dataclass(frozen=True)
class EvaluationRow:
    group: str
    question: str
    score: float | None
    source: str
    section: str
    content: str


def load_test_questions() -> dict[str, list[str]]:
    with TEST_QUESTIONS_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        group: [str(question) for question in data.get(group, [])]
        for group in TEST_GROUPS
    }


def evaluate(top_k: int) -> list[EvaluationRow]:
    service = RagService()
    questions = load_test_questions()
    rows: list[EvaluationRow] = []

    for group in TEST_GROUPS:
        for question in questions[group]:
            results = service.retrieve(question, top_k=top_k)
            top_result = results[0] if results else None

            rows.append(
                EvaluationRow(
                    group=group,
                    question=question,
                    score=top_result.score if top_result else None,
                    source=top_result.source if top_result else "",
                    section=top_result.section if top_result else "",
                    content=top_result.content if top_result else "",
                )
            )

    return rows


def print_report(rows: list[EvaluationRow], show_content: bool) -> None:
    for group in TEST_GROUPS:
        group_rows = [row for row in rows if row.group == group]
        print(f"\n=== {group} ({len(group_rows)} 題) ===")

        for row in group_rows:
            score = f"{row.score:.4f}" if row.score is not None else "N/A"
            print(f"{score} | {row.question}")
            print(f"       -> {row.source} / {row.section}")
            if show_content:
                preview = " ".join(row.content.split())[:160]
                print(f"       -> {preview}")

        scores = [row.score for row in group_rows if row.score is not None]
        if scores:
            print(
                "分數摘要："
                f"min={min(scores):.4f}, "
                f"avg={mean(scores):.4f}, "
                f"max={max(scores):.4f}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="批次評估個人知識庫檢索結果")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--show-content", action="store_true")
    args = parser.parse_args()

    rows = evaluate(top_k=args.top_k)
    print_report(rows, show_content=args.show_content)


if __name__ == "__main__":
    main()