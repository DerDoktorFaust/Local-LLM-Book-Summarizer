import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from extractor import extract_pages
from chunker import chunk_pages
from classifier import classify_document

try:
    from llm import load_model, unload_model, MODEL_PATH
except ImportError:
    from llm import load_model, unload_model
    MODEL_PATH = None

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


def setup_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = logs_dir / f"run_{timestamp}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return log_path


def validate_pdf_path(pdf_path):
    if not pdf_path.exists():
        raise FileNotFoundError(f"Input file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise ValueError(f"Input path is not a file: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Input file must be a PDF: {pdf_path}")

    if pdf_path.stat().st_size == 0:
        raise ValueError(f"Input PDF is empty: {pdf_path}")


def validate_pages(pages):
    if not pages:
        raise ValueError(
            "PDF extraction produced no pages. "
            "The PDF may be image-only, encrypted, corrupted, or not OCR'd."
        )

    pages_with_text = [
        page for page in pages
        if page.get("text") and page["text"].strip()
    ]

    if not pages_with_text:
        raise ValueError(
            "PDF extraction produced pages, but no extractable text. "
            "This usually means the PDF needs OCR first."
        )

    return pages_with_text


def validate_chunks(chunks):
    if not chunks:
        raise ValueError(
            "Chunking produced no chunks. "
            "Check whether text extraction succeeded."
        )

    for i, chunk in enumerate(chunks, start=1):
        if "text" not in chunk or not chunk["text"].strip():
            raise ValueError(f"Chunk {i} has no text.")

        if "start_page" not in chunk or "end_page" not in chunk:
            raise ValueError(f"Chunk {i} is missing page range metadata.")


def validate_llm_response(response, stage):
    if response is None:
        raise ValueError(f"{stage} returned no response.")

    if not isinstance(response, str):
        raise TypeError(
            f"{stage} returned {type(response).__name__}, expected string."
        )

    if not response.strip():
        raise ValueError(f"{stage} returned an empty response.")

    return response.strip()


def format_duration(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes} min {remaining_seconds} sec"


def main():
    args = parse_args()
    log_path = setup_logging()

    start_time = time.time()
    errors = 0
    model_loaded = False

    pdf_path = Path(args.pdf)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    logging.info("Starting Local LLM Book & Article Summarizer")
    logging.info(f"Log file: {log_path}")
    logging.info(f"Input file: {pdf_path}")

    if MODEL_PATH:
        logging.info(f"Model path: {MODEL_PATH}")
    else:
        logging.info("Model path: not available from config.yaml")

    try:
        try:
            validate_pdf_path(pdf_path)
        except Exception as e:
            logging.error(f"Input validation failed: {e}")
            return

        try:
            logging.info("\nExtracting PDF text...")
            pages = extract_pages(pdf_path)
            pages = validate_pages(pages)
            total_pages = len(pages)
            logging.info(f"Extracted text from {total_pages} pages.")
        except Exception as e:
            logging.exception(
                "PDF extraction failed. The file may be image-only, encrypted, "
                "corrupted, or not OCR'd."
            )
            logging.error(f"Clear error: {e}")
            return

        try:
            document_type = classify_document(total_pages)
            logging.info(f"Document type: {document_type}")
        except Exception as e:
            logging.exception("Document classification failed.")
            logging.error(f"Clear error: {e}")
            return

        output_path = output_dir / f"{pdf_path.stem}_{document_type}_summary.md"

        try:
            logging.info("\nChunking text...")
            chunks = chunk_pages(pages)
            validate_chunks(chunks)
        except Exception as e:
            logging.exception("Chunking failed.")
            logging.error(f"Clear error: {e}")
            return

        total_chunks = len(chunks)
        total_chars = sum(len(c["text"]) for c in chunks)
        est_tokens = int(total_chars / 4)

        logging.info("\n--- Pipeline Stats ---")
        logging.info(f"Input file: {pdf_path}")
        logging.info(f"Pages: {total_pages}")
        logging.info(f"Document type: {document_type}")
        logging.info(f"Chunks: {total_chunks}")
        logging.info(f"Estimated tokens: {est_tokens}")

        chunk_lengths = [len(c["text"]) for c in chunks]

        logging.info("\n--- Chunk Stats ---")
        logging.info(f"Avg chars per chunk: {sum(chunk_lengths) // len(chunk_lengths)}")
        logging.info(f"Min chars: {min(chunk_lengths)}")
        logging.info(f"Max chars: {max(chunk_lengths)}")

        try:
            logging.info("\nLoading LLM once for entire run...")
            load_model()
            model_loaded = True
            logging.info("LLM loaded successfully.")
        except Exception as e:
            logging.exception("LLM loading failed.")
            logging.error(
                "Clear error: The local model could not be loaded. "
                "Check model_path in config.yaml, model compatibility, and available RAM."
            )
            logging.error(f"Original error: {e}")
            return

        chunk_summaries = []
        chunk_times = []

        for i, chunk in enumerate(chunks):
            chunk_start = time.time()
            page_range = f"{chunk['start_page']}–{chunk['end_page']}"

            logging.info(
                f"\nSummarizing chunk {i + 1}/{total_chunks} "
                f"(pages {page_range})..."
            )

            try:
                summary = summarize_chunk(chunk)
                summary = validate_llm_response(
                    summary,
                    f"Chunk {i + 1} summary",
                )

                compressed_notes = extract_compressed_notes(summary)
                compressed_notes = validate_llm_response(
                    compressed_notes,
                    f"Chunk {i + 1} compressed notes",
                )

            except Exception as e:
                logging.exception(
                    f"LLM response issue on chunk {i + 1} "
                    f"(pages {page_range})."
                )
                logging.error(f"Clear error: {e}")
                errors += 1
                continue

            chunk_time = time.time() - chunk_start
            chunk_times.append(chunk_time)

            logging.info(f"Chunk {i + 1} took {chunk_time:.2f} seconds")

            chunk_summaries.append({
                "chunk": chunk,
                "summary": summary,
                "compressed_notes": compressed_notes,
            })

        if not chunk_summaries:
            logging.error(
                "\nNo chunk summaries were created. "
                "The LLM may be failing to return usable text."
            )
            logging.error(f"Errors: {errors}")
            return

        if chunk_times:
            logging.info("\n--- LLM Timing ---")
            logging.info(f"Avg chunk time: {sum(chunk_times) / len(chunk_times):.2f}s")
            logging.info(f"Slowest chunk: {max(chunk_times):.2f}s")
            logging.info(f"Fastest chunk: {min(chunk_times):.2f}s")

        if document_type == "article":
            logging.info("\nGenerating final article summary...")
            batch_summaries = []

            try:
                final_summary = synthesize_article_summary(chunk_summaries)
                final_summary = validate_llm_response(
                    final_summary,
                    "Final article summary",
                )
            except Exception as e:
                logging.exception("Final article summary failed.")
                logging.error(f"Clear error: {e}")
                final_summary = (
                    "Final article-level summary failed. "
                    "Chunk summaries were still generated successfully."
                )
                errors += 1

            logging.info("\nVerifying final article summary...")

            try:
                verification_report = verify_article_summary(
                    final_summary,
                    chunk_summaries,
                )
                verification_report = validate_llm_response(
                    verification_report,
                    "Article verification report",
                )
            except Exception as e:
                logging.exception("Article verification failed.")
                logging.error(f"Clear error: {e}")
                verification_report = (
                    "Verification failed. Review the final summary against "
                    "the chunk summaries manually."
                )
                errors += 1

        else:
            logging.info("\nSynthesizing batch summaries...")

            try:
                batch_summaries = synthesize_batches(
                    chunk_summaries,
                    batch_size=6,
                )

                if not isinstance(batch_summaries, list):
                    raise TypeError(
                        "Batch synthesis returned a non-list object."
                    )

                logging.info(f"Created {len(batch_summaries)} intermediate summaries")

            except Exception as e:
                logging.exception("Batch summary generation failed.")
                logging.error(f"Clear error: {e}")
                batch_summaries = []
                errors += 1

            logging.info("\nGenerating final book summary...")

            try:
                if batch_summaries:
                    final_summary = synthesize_final_summary(batch_summaries)
                    final_summary = validate_llm_response(
                        final_summary,
                        "Final book summary",
                    )
                else:
                    final_summary = (
                        "Final book-level summary failed because no batch summaries "
                        "were created. Chunk summaries were still generated successfully."
                    )
            except Exception as e:
                logging.exception("Final book summary failed.")
                logging.error(f"Clear error: {e}")
                final_summary = (
                    "Final book-level summary failed. "
                    "Chunk summaries and any completed batch summaries were still "
                    "generated successfully."
                )
                errors += 1

            logging.info("\nVerifying final book summary...")

            try:
                if batch_summaries:
                    verification_report = verify_final_summary(
                        final_summary,
                        batch_summaries,
                    )
                    verification_report = validate_llm_response(
                        verification_report,
                        "Book verification report",
                    )
                else:
                    verification_report = (
                        "Verification skipped because no batch summaries were created."
                    )
            except Exception as e:
                logging.exception("Book verification failed.")
                logging.error(f"Clear error: {e}")
                verification_report = (
                    "Verification failed. Review the final summary against the chunk "
                    "and batch summaries manually."
                )
                errors += 1

        logging.info("\n--- Output ---")
        logging.info(f"Final summary length (chars): {len(final_summary)}")

        try:
            write_markdown_output(
                final_summary=final_summary,
                verification_report=verification_report,
                batch_summaries=batch_summaries,
                chunk_summaries=chunk_summaries,
                output_path=output_path,
                source_file=pdf_path.name,
                model_name=str(MODEL_PATH) if MODEL_PATH else None,
                work_type=document_type,
            )
        except TypeError:
            write_markdown_output(
                final_summary=final_summary,
                verification_report=verification_report,
                batch_summaries=batch_summaries,
                chunk_summaries=chunk_summaries,
                output_path=output_path,
            )
        except Exception as e:
            logging.exception("Markdown file writing failed.")
            logging.error(
                "Clear error: The summaries were generated, but the output file "
                "could not be written. Check the output directory and file permissions."
            )
            logging.error(f"Original error: {e}")
            return

        total_time = time.time() - start_time
        tokens_per_sec = est_tokens / total_time if total_time > 0 else 0

        logging.info("\n--- Throughput ---")
        logging.info(f"Tokens/sec (est): {tokens_per_sec:.2f}")
        logging.info(f"Errors: {errors}")
        logging.info(f"Markdown summary saved to: {output_path}")
        logging.info(f"Log saved to: {log_path}")
        logging.info(f"Total processing time: {format_duration(total_time)}")

    finally:
        if model_loaded:
            try:
                logging.info("\nUnloading LLM...")
                unload_model()
                logging.info("LLM unloaded successfully.")
            except Exception as e:
                logging.exception("LLM unload failed.")
                logging.error(f"Clear error: {e}")


if __name__ == "__main__":
    main()