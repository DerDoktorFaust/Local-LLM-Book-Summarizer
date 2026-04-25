import time
from pathlib import Path

from extractor import extract_pages
from chunker import chunk_pages
from llm import generate


def summarize_chunk(chunk):
    prompt = f"""
Summarize the following text from pages {chunk['start_page']}–{chunk['end_page']}.

Focus on:
- Main argument
- Key evidence
- Important concepts
- Relevance for a historian

Text:
{chunk['text']}
"""
    return generate(prompt)


def write_markdown_output(final_summary, chunk_summaries, output_path):
    lines = []

    lines.append("# Book Summary\n")
    lines.append(final_summary)
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
        except Exception as e:
            print(f"Error on chunk {i + 1}: {e}")
            errors += 1
            continue

        chunk_time = time.time() - chunk_start
        chunk_times.append(chunk_time)

        print(f"Chunk {i + 1} took {chunk_time:.2f} seconds")

        chunk_summaries.append({
            "chunk": chunk,
            "summary": summary
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

    combined = "\n\n".join(
        [
            f"Pages {s['chunk']['start_page']}–{s['chunk']['end_page']}:\n{s['summary'][:1500]}"
            for s in chunk_summaries
        ]
    )

    final_prompt = f"""
Based on the following page-referenced chunk summaries, produce a coherent analytical summary of the entire book.

Include:
- One-sentence thesis
- Main argument
- Chapter or section structure if apparent
- Key evidence
- Important concepts
- Historiographical significance
- Strengths and weaknesses
- Questions for further reading

Chunk summaries:
{combined}
"""

    print("\nGenerating final book summary...")
    
    try:
        final_summary = generate(final_prompt)
    except Exception as e:
        print(f"Error generating final summary: {e}")
        final_summary = "Final book level summary failed. Chunk summaries were still generated successfully."
        errors += 1

    final_length = len(final_summary)

    print("\n--- Output ---")
    print(f"Final summary length (chars): {final_length}")

    write_markdown_output(final_summary, chunk_summaries, output_path)

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