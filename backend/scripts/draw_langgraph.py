import argparse
from pathlib import Path

from app.graph.builder import get_support_graph

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPO_ROOT / "docs" / "generated" / "current-langgraph.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw the current supportflow LangGraph and store it locally."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output path. Use .md for a rendered Mermaid Markdown document.",
    )
    return parser.parse_args()


def render_mermaid() -> str:
    return get_support_graph().get_graph().draw_mermaid()


def render_markdown(mermaid: str) -> str:
    return "\n".join(
        [
            "# Current LangGraph",
            "",
            "Generated from `backend/app/graph/builder.py`.",
            "",
            "```mermaid",
            mermaid.strip(),
            "```",
            "",
        ]
    )


def write_graph_diagram(output_path: Path) -> Path:
    mermaid = render_mermaid()
    content = render_markdown(mermaid) if output_path.suffix == ".md" else mermaid + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    return output_path


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    args = parse_args()
    path = write_graph_diagram(args.output)
    print(f"wrote {_display_path(path)}")


if __name__ == "__main__":
    main()
