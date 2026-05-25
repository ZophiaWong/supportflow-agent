from scripts.draw_langgraph import write_graph_diagram


def test_write_graph_diagram_generates_current_mermaid_markdown(tmp_path) -> None:
    output_path = tmp_path / "current-langgraph.md"

    write_graph_diagram(output_path)

    content = output_path.read_text()
    assert "```mermaid" in content
    assert "load_ticket_context" in content
    assert "risk_gate" in content
    assert "human_review_interrupt" in content
    assert "manual_takeover" in content
    assert "risk_gate -.-> finalize_reply" in content
    assert "risk_gate -.-> human_review_interrupt" in content
    assert "apply_review_decision -.-> manual_takeover" in content
