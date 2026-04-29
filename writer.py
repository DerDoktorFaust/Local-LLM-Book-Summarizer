def write_markdown_output(
    final_summary,
    verification_report,
    batch_summaries,
    chunk_summaries,
    output_path,
):
    lines = []

    lines.append("# Summary\n")

    lines.append("## Final Summary\n")
    lines.append(final_summary)
    lines.append("\n---\n")

    lines.append("## Verification Report\n")
    lines.append(verification_report)
    lines.append("\n---\n")

    lines.append("## Intermediate Batch Summaries\n")

    for i, batch in enumerate(batch_summaries, start=1):
        lines.append(f"### Batch {i}: Pages {batch['start_page']}–{batch['end_page']}\n")
        lines.append(batch["summary"])
        lines.append("\n---\n")

    lines.append("## Chunk Summaries\n")

    for i, item in enumerate(chunk_summaries, start=1):
        chunk = item["chunk"]
        summary = item["summary"]

        lines.append(f"### Chunk {i}: Pages {chunk['start_page']}–{chunk['end_page']}\n")
        lines.append(summary)
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
