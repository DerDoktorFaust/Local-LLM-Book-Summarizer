# Local LLM Book & Article Summarizer

## Purpose

Summarizing long-form texts with large language models presents two core problems:

1. **Context limitations** – Even with large context windows, models struggle to maintain coherence across entire books.
2. **Privacy and copyright concerns** – Uploading full texts to external APIs is often undesirable or legally questionable.

This project solves both by running entirely **locally** and using a **hierarchical summarization pipeline** that processes documents in structured stages.

---

## Key Features

- Fully local pipeline (no external API calls required)
- Supports both **books and articles**
- Automatic document classification (based on length)
- Hierarchical summarization for long texts
- Page-referenced outputs
- Built-in verification pass to reduce hallucination and overstatement
- Modular architecture for easy extension

---

## How It Works

### 1. Input

- OCR’d PDF (text must be extractable)
- Works best with clean, structured PDFs

---

### 2. Extraction

- Uses PyMuPDF to extract text **page by page**
- Preserves page boundaries for citation

---

### 3. Chunking

- Splits text into manageable chunks
- Each chunk includes:
  - `start_page`
  - `end_page`
  - `text`

---

### 4. Document Classification

The system automatically determines whether the PDF is:

- **Article** (≤ ~40 pages)
- **Book** (> ~40 pages)

This decision controls the summarization pipeline.

---

### 5. Chunk-Level Summarization

Each chunk is processed by a local LLM with strict constraints:

- Conservative, text-faithful summaries
- Explicit page references
- No overgeneralization or inflated claims

Each chunk produces:
- Full summary
- Compressed notes (used for synthesis)

---

### 6. Hierarchical Synthesis

#### Articles

```
Chunks → Final Article Summary → Verification
```

#### Books

```
Chunks → Batch Summaries → Final Book Summary → Verification
```

Batching prevents loss of coherence across long texts.

---

### 7. Verification Pass

A second LLM pass evaluates the final summary for:

- Overstatements
- Unsupported claims
- Missing evidence
- Incorrect structure

This produces a **verification report**, not a rewrite.

---

### 8. Output

Markdown file containing:

- Final summary
- Verification report
- Intermediate batch summaries (books only)
- All chunk summaries

Example output:

```
output/book_summary.md
output/article_summary.md
```

---

## Project Structure

```
book-summarizer/
├── main.py          # Pipeline orchestration
├── llm.py           # Model loading and inference
├── summarizer.py    # Summarization logic
├── prompts.py       # All LLM prompts
├── writer.py        # Markdown output
├── extractor.py     # PDF text extraction
├── chunker.py       # Chunking logic
├── classifier.py    # Article vs book classification
├── input/
├── output/
└── requirements.txt
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/book-summarizer.git
cd book-summarizer
```

### 2. Create environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage



### 1. Run the pipeline

```bash
python main.py yourfile.pdf
```

---

### 2. Output

Results will appear in:

```
output/
```

---

## Design Philosophy

- **Precision over fluency** – Avoid polished but inaccurate summaries
- **Traceability** – Always anchor claims to page ranges
- **Modularity** – Each component is independent and replaceable
- **Local-first** – No dependency on external APIs

---

## Limitations

- Requires OCR’d PDFs (no image-only scans)
- Page-based chunking ignores deeper document structure (chapters/sections)
- Quality depends on the underlying local model
- Not a substitute for close reading

---

## Future Improvements

- Better document classification (beyond page count)
- Chapter/section-aware chunking
- GUI or macOS app frontend
- Integration with research tools (Zotero, Obsidian)
- Multi-model pipelines (OCR → translation → summarization)

---

## Use Case

Designed for researchers (especially historians) who need:

- Rapid orientation in long texts
- Structured, argument-aware summaries
- Local, private processing of PDFs

---

## License

MIT