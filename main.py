import time
from pathlib import Path

from extractor import extract_pages
from chunker import chunk_pages
from llm import generate


def summarize_chunk(chunk):
    prompt = f"""
Summarize the following text from pages {chunk['start_page']}–{chunk['end_page']}.

STRICT REQUIREMENTS:
- Do NOT generalize beyond what is stated
- Do NOT strengthen claims
- Avoid words like "collapse," "complete," "entirely," or "proves" unless explicitly supported
- Stay close to the author's actual argument and language
- Be precise rather than sweeping
- Every major claim must include page references
- If a claim is uncertain or inferred, mark it with "(uncertain)" or "(inferred)"
- If unsure, hedge rather than assert

Output TWO sections:

## Full Summary
Maximum 300 words
Include:
- Main claim in this section
- 2–3 specific pieces of evidence, with page references
- Key terms or concepts introduced
- Any tensions, qualifications, or limits in the argument

## Compressed Notes

Maximum 150 words.

Include:
- Main claim
- 2–3 concrete pieces of evidence
- Key terms, using the author's language where possible
- Page references
- Any uncertainty marked clearly

Text:
{chunk['text']}
"""
    return generate(prompt)


def extract_compressed_notes(summary):
    marker = "## Compressed Notes"

    if marker in summary:
        return summary.split(marker, 1)[1].strip()

    return summary[:1200].strip()


def synthesize_batches(chunk_summaries, batch_size=6):
    batch_summaries = []

    for i in range(0, len(chunk_summaries), batch_size):
        batch = chunk_summaries[i:i + batch_size]

        combined = "\n\n".join(
            [
                (
                    f"Pages {s['chunk']['start_page']}–{s['chunk']['end_page']}:\n"
                    f"{s['compressed_notes']}"
                )
                for s in batch
            ]
        )

        prompt = f"""
The following are compressed notes from consecutive chunks of a book/article.

Produce a conservative intermediate synthesis.

STRICT REQUIREMENTS:
- Do NOT exaggerate or extend the author's claims
- Do NOT make the argument cleaner or more linear than the notes support
- Avoid words like "collapse," "complete," "entirely," or "proves" unless explicitly supported
- Preserve ambiguity, tension, contradiction, and uncertainty
- Every major claim must include page references
- If a claim is uncertain or inferred, mark it with "(uncertain)" or "(inferred)"
- If unsure, hedge rather than assert

Include:
- Main claim across these chunks
- Argument progression, if clearly present
- 3–5 specific pieces of evidence with page references
- Key terms or concepts
- Tensions, qualifications, or limits in the argument
- Page ranges to revisit

Compressed notes:
{combined}
"""

        batch_summary = generate(prompt)

        start_page = batch[0]["chunk"]["start_page"]
        end_page = batch[-1]["chunk"]["end_page"]

        batch_summaries.append({
            "start_page": start_page,
            "end_page": end_page,
            "summary": batch_summary
        })

    return batch_summaries


def synthesize_final_summary(batch_summaries):
    combined = "\n\n".join(
        [
            f"Pages {b['start_page']}–{b['end_page']}:\n{b['summary']}"
            for b in batch_summaries
        ]
    )

    prompt = f"""
Based on the following intermediate summaries, produce an analytical summary of the entire work.

STRICT REQUIREMENTS:
- Do NOT exaggerate or extend the author's claims
- Avoid words like "collapse," "complete," "entirely," or "proves" unless explicitly supported
- Preserve ambiguity, tension, and contradiction where they exist
- Do NOT impose an overly clean or linear structure if the argument is messy
- Every major claim must include page references
- If a claim is uncertain or inferred, mark it with "(uncertain)" or "(inferred)"
- If unsure, hedge rather than assert

Include:
- One-sentence thesis, accurate and not inflated
- Main argument
- Structure of the argument, only if clearly present
- At least 3 specific pieces of evidence from the text with page references
- Key concepts, using the author's terms where possible
- Historiographical contribution, precisely stated
- Important tensions, qualifications, or limits

Be conservative, precise, and text-faithful rather than elegant.

Intermediate summaries:
{combined}
"""

    return generate(prompt)


def verify_final_summary(final_summary, batch_summaries):
    combined = "\n\n".join(
        [
            f"Pages {b['start_page']}–{b['end_page']}:\n{b['summary']}"
            for b in batch_summaries
        ]
    )

    prompt = f"""
Evaluate the final summary against the intermediate summaries.

Your task is NOT to rewrite the summary. Your task is to identify reliability problems.

Check for:
- Overstatements
- Unsupported claims
- Missing major evidence
- Misinterpretations
- Overly clean or linear framing
- Claims that need more hedging
- Missing page references

Be critical, specific, and concise.

For each issue, include:
- Problem
- Why it is a problem
- Suggested correction

Final summary:
{final_summary}

Intermediate summaries:
{combined}
"""

    return generate(prompt)


def write_markdown_output(
    final_summary,
    verification_report,
    batch_summaries,
    chunk_summaries,
    output_path
):
    lines = []

    lines.append("# Book Summary\n")

    lines.append("## Final Summary\n")
    lines.append(final_summary)
    lines.append("\n---\n")

    lines.append("## Verification Report\n")
    lines.append(verification_report)
    lines.append("\n---\n")

    lines.append("## Intermediate Batch Summaries\n")

    for i, batch in enumerate(batch_summaries, start=1):
        lines.append(
            f"### Batch {i}: Pages {batch['start_page']}–{batch['end_page']}\n"
        )
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


def main():
    start_time = time.time()
    errors = 0

    pdf_path = Path("book.pdf")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "book_summary.md"

    print("Extracting...")
    pages = extract_pages(pdf_path)

    print("Chunking...")
    chunks = chunk_pages(pages)

    total_pages = len(pages)
    total_chunks = len(chunks)
    total_chars = sum(len(c["text"]) for c in chunks)
    est_tokens = int(total_chars / 4)

    print("\n--- Pipeline Stats ---")
    print(f"Pages: {total_pages}")
    print(f"Chunks: {total_chunks}")
    print(f"Estimated tokens: {est_tokens}")

    if chunks:
        chunk_lengths = [len(c["text"]) for c in chunks]

        print("\n--- Chunk Stats ---")
        print(f"Avg chars per chunk: {sum(chunk_lengths) // len(chunk_lengths)}")
        print(f"Min chars: {min(chunk_lengths)}")
        print(f"Max chars: {max(chunk_lengths)}")
    else:
        print("No chunks created. Exiting.")
        return

    chunk_summaries = []
    chunk_times = []

    for i, chunk in enumerate(chunks):
        chunk_start = time.time()

        print(f"\nSummarizing chunk {i + 1}/{len(chunks)}...")

        try:
            summary = summarize_chunk(chunk)
            compressed_notes = extract_compressed_notes(summary)
        except Exception as e:
            print(f"Error on chunk {i + 1}: {e}")
            errors += 1
            continue

        chunk_time = time.time() - chunk_start
        chunk_times.append(chunk_time)

        print(f"Chunk {i + 1} took {chunk_time:.2f} seconds")

        chunk_summaries.append({
            "chunk": chunk,
            "summary": summary,
            "compressed_notes": compressed_notes
        })

    if not chunk_summaries:
        print("\nNo chunk summaries created. Exiting.")
        print(f"Errors: {errors}")
        return

    if chunk_times:
        print("\n--- LLM Timing ---")
        print(f"Avg chunk time: {sum(chunk_times) / len(chunk_times):.2f}s")
        print(f"Slowest chunk: {max(chunk_times):.2f}s")
        print(f"Fastest chunk: {min(chunk_times):.2f}s")

    print("\nSynthesizing batch summaries...")

    try:
        batch_summaries = synthesize_batches(chunk_summaries, batch_size=6)
        print(f"Created {len(batch_summaries)} intermediate summaries")
    except Exception as e:
        print(f"Error generating batch summaries: {e}")
        batch_summaries = []
        errors += 1

    print("\nGenerating final book summary...")

    try:
        if batch_summaries:
            final_summary = synthesize_final_summary(batch_summaries)
        else:
            final_summary = (
                "Final book-level summary failed because no batch summaries were created. "
                "Chunk summaries were still generated successfully."
            )
    except Exception as e:
        print(f"Error generating final summary: {e}")
        final_summary = (
            "Final book-level summary failed. "
            "Chunk summaries and any completed batch summaries were still generated successfully."
        )
        errors += 1

    print("\nVerifying final summary...")

    try:
        if batch_summaries:
            verification_report = verify_final_summary(final_summary, batch_summaries)
        else:
            verification_report = (
                "Verification skipped because no batch summaries were created."
            )
    except Exception as e:
        print(f"Error verifying final summary: {e}")
        verification_report = (
            "Verification failed. Review the final summary against the chunk and batch summaries manually."
        )
        errors += 1

    final_length = len(final_summary)

    print("\n--- Output ---")
    print(f"Final summary length (chars): {final_length}")

    write_markdown_output(
        final_summary=final_summary,
        verification_report=verification_report,
        batch_summaries=batch_summaries,
        chunk_summaries=chunk_summaries,
        output_path=output_path
    )

    total_time = time.time() - start_time
    tokens_per_sec = est_tokens / total_time if total_time > 0 else 0

    minutes = int(total_time // 60)
    seconds = int(total_time % 60)

    print("\n--- Throughput ---")
    print(f"Tokens/sec (est): {tokens_per_sec:.2f}")

    print(f"\nErrors: {errors}")
    print(f"Markdown summary saved to: {output_path}")
    print(f"Total processing time: {minutes} min {seconds} sec")


if __name__ == "__main__":
    main()