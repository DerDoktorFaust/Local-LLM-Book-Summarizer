# Local LLM Book & Article Summarizer

## Purpose

Summarizing long-form texts with large language models presents two core problems:

1. Context limitations – Even with large context windows, models struggle to maintain coherence across entire books.
2. Privacy and copyright concerns – Uploading full texts to external APIs is often undesirable or legally questionable.

This project solves both by running entirely locally and using a hierarchical summarization pipeline that processes documents in structured stages.

---

## Key Features

- Fully local pipeline (no external API calls required)
- Supports both books and articles
- Page-referenced outputs for traceability
- Hierarchical summarization for long texts
- Built-in verification pass to reduce hallucination and overstatement
- Modular architecture for easy extension
- Structured Markdown output with YAML front matter for reuse in research workflows

---

## How It Works

### 1. Input

- OCR’d PDF (text must be extractable)
- Works best with clean, structured PDFs

---

### 2. Extraction

- Uses PyMuPDF to extract text page by page
- Preserves page boundaries for citation

---

### 3. Chunking

- Splits text into manageable chunks
- Each chunk includes:
  - start_page
  - end_page
  - embedded page markers ([PAGE X] ... [/PAGE X])
- Ensures all summaries can be traced back to the original text

---

### 4. Chunk-Level Summarization

Each chunk is processed by a local LLM with strict constraints:

- Conservative, text-faithful summaries
- Explicit page references
- No overgeneralization or inflated claims

Each chunk produces:
- Structured analytical summary
- Compressed notes (used for synthesis)

---

### 5. Hierarchical Synthesis

#### Articles

Chunks → Final Article Summary → Verification

#### Books

Chunks → Batch Summaries → Final Book Summary → Verification

Batching prevents loss of coherence across long texts.

---

### 6. Verification Pass

A second LLM pass evaluates the final summary for:

- Overstatements
- Unsupported claims
- Missing structure
- Invented historiography

This produces a verification report, not a rewrite.

---

### 7. Output

Markdown file containing:

- YAML front matter (metadata-ready)
- Final structured summary
- Verification report
- Intermediate batch summaries (books)
- All chunk summaries with page ranges

Example output:

output/book_summary.md output/article_summary.md

---

## Project Structure

book-summarizer/
├── main.py          # Pipeline orchestration
├── llm.py           # Model loading and inference
├── summarizer.py    # Summarization logic
├── prompts.py       # All LLM prompts
├── writer.py        # Markdown output
├── extractor.py     # PDF text extraction
├── chunker.py       # Chunking logic
├── classifier.py    # (Planned) document classification
├── input/
├── output/
└── requirements.txt
---

## Installation

### 1. Clone the repository

bash git clone https://github.com/YOUR_USERNAME/book-summarizer.git cd book-summarizer 

### 2. Create environment

bash python3 -m venv venv source venv/bin/activate 

### 3. Install dependencies

bash pip install -r requirements.txt 

---

## Local LLM Requirement (MLX)

This project requires a locally running LLM compatible with Apple MLX.

The pipeline does NOT use external APIs. You must have a model installed locally and configured in llm.py.

### Requirements

- Apple Silicon Mac (M-series recommended)
- MLX-compatible model (e.g. Gemma, Qwen, etc.)
- Model stored locally on your machine

Example model path (set in llm.py):

/Users/yourname/.lmstudio/models/mlx-community/your-model-name

### Important

- The model is loaded directly in Python (no server required)
- The model must fit in your available RAM
- Performance and output quality depend heavily on the model you choose

### Recommended Models

- ~7B–12B parameter models for stability and speed
- Larger models may exceed memory limits depending on your system

---

## Usage

### 1. Run the pipeline

bash python main.py yourfile.pdf 

### 2. Output

Results will appear in:

output/

---

## Output Format

Each .md file includes:

### YAML Front Matter

yaml title: null author: null publication_year: null publisher_or_journal: null work_type: null source_file: yourfile.pdf model: your_model_path model_provider: null generated_at: timestamp pipeline_version: "0.1" 

### Structured Sections

- Final Summary
- Verification Report
- Intermediate Summaries
- Chunk Summaries (with page ranges)

This format is designed for:

- Obsidian
- DEVONthink
- RAG pipelines
- Future database integration

---

## Design Philosophy

- Precision over fluency – Avoid polished but inaccurate summaries
- Traceability – All claims tied to page ranges
- Modularity – Each component is independent and replaceable
- Local-first – No dependency on external APIs
- Structured output – Designed for reuse in research workflows

---

## Limitations

- Requires OCR’d PDFs (no image-only scans)
- Page-based chunking ignores deeper document structure (chapters/sections)
- Quality depends heavily on the underlying local model
- Smaller models may struggle with complex arguments
- Not a substitute for close reading

---

## Future Improvements

- Robust document classification (beyond page count)
- Chapter/section-aware chunking
- Automatic bibliographic metadata extraction
- GUI or macOS native app
- Integration with research tools (Zotero, Obsidian)
- Multi-model pipelines (OCR → translation → summarization)

---

## Use Case

Designed for researchers (especially historians) who need:

- Rapid orientation in long texts
- Structured, argument-aware summaries
- Traceable claims with page references
- Local, private processing of PDFs

---

## License

MIT