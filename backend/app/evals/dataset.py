import json
from pathlib import Path

from app.evals.schemas import EvalExample


def load_eval_dataset(path: Path) -> list[EvalExample]:
    examples: list[EvalExample] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
        examples.append(EvalExample.model_validate(payload))

    if not examples:
        raise ValueError(f"Eval dataset is empty: {path}")
    return examples
