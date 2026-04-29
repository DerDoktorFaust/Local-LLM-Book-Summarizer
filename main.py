import argparse
import time
from pathlib import Path

from extractor import extract_pages
from chunker import chunk_pages
from classifier import classify_document
from llm import load_model, unload_model

from summarizer import (
    summarize_chunk,
    extract_compressed_notes,
    synthesize_batches,
    synthesize_final_summary,
    verify_final_summary,
    synthesize_article_summary,
    verify_article_summary,
)

from writer import write_markdown_output


def parse_args():
    parser = argparse.ArgumentParser(
        description="Local LLM Book & Article Summarizer"
    )

    parser.add_argument(
        "pdf",
        type=str,
        help="Path to the input PDF file",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    start_time = time.time()
    errors = 0

    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Input file must be a PDF: {pdf_path}")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    try:
        print("Extracting...")
        pages = extract_pages(pdf_path)

        total_pages = len(pages)
        document_type = classify_document(total_pages)

        output_path = output_dir / f"{pdf_path.stem}_{document_type}_summary.md"

        print(f"Document type: {document_type}")

        print("Chunking...")
        chunks = chunk_pages(pages)

        total_chunks = len(chunks)
        total_chars = sum(len(c["text"]) for c in chunks)
        est_tokens = int(total_chars / 4)

        print("\n--- Pipeline Stats ---")
        print(f"Input file: {pdf_path}")
        print(f"Pages: {total_pages}")
        print(f"Document type: {document_type}")
        print(f"Chunks: {total_chunks}")
        print(f"Estimated tokens: {est_tokens}")

        if not chunks:
            print("No chunks created. Exiting.")
            return

        chunk_lengths = [len(c["text"]) for c in chunks]

        print("\n--- Chunk Stats ---")
        print(f"Avg chars per chunk: {sum(chunk_lengths) // len(chunk_lengths)}")
        print(f"Min chars: {min(chunk_lengths)}")
        print(f"Max chars: {max(chunk_lengths)}")

        print("\nLoading LLM once for entire run...")
        load_model()

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
                "compressed_notes": compressed_notes,
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

        if document_type == "article":
            print("\nGenerating final article summary...")

            batch_summaries = []

            try:
                final_summary = synthesize_article_summary(chunk_summaries)
            except Exception as e:
                print(f"Error generating article summary: {e}")
                final_summary = (
                    "Final article-level summary failed. "
                    "Chunk summaries were still generated successfully."
                )
                errors += 1

            print("\nVerifying final article summary...")

            try:
                verification_report = verify_article_summary(
                    final_summary,
                    chunk_summaries,
                )
            except Exception as e:
                print(f"Error verifying article summary: {e}")
                verification_report = (
                    "Verification failed. Review the final summary against "
                    "the chunk summaries manually."
                )
                errors += 1

        else:
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
                        "Final book-level summary failed because no batch summaries "
                        "were created. Chunk summaries were still generated successfully."
                    )
            except Exception as e:
                print(f"Error generating final summary: {e}")
                final_summary = (
                    "Final book-level summary failed. "
                    "Chunk summaries and any completed batch summaries were still "
                    "generated successfully."
                )
                errors += 1

            print("\nVerifying final book summary...")

            try:
                if batch_summaries:
                    verification_report = verify_final_summary(
                        final_summary,
                        batch_summaries,
                    )
                else:
                    verification_report = (
                        "Verification skipped because no batch summaries were created."
                    )
            except Exception as e:
                print(f"Error verifying final summary: {e}")
                verification_report = (
                    "Verification failed. Review the final summary against the chunk "
                    "and batch summaries manually."
                )
                errors += 1

        print("\n--- Output ---")
        print(f"Final summary length (chars): {len(final_summary)}")

        write_markdown_output(
            final_summary=final_summary,
            verification_report=verification_report,
            batch_summaries=batch_summaries,
            chunk_summaries=chunk_summaries,
            output_path=output_path,
            document_type=document_type,
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

    finally:
        unload_model()


if __name__ == "__main__":
    main()