# Local LLM Book Summarizer

## Purpose
Summarizing entire books remains a challenging task for large language models. The first issue are context windows. Though frontier models have increased their window sizes, it remains that these models find it difficult to "hold everything together" after a certain point. Entire books with 100k or 250k tokens fit into massive new context windows of 1 million or more, but the models cannot handle it all without errors and hallucinations. The second issue involves copyright infringement. Uploading entire books to frontier models and their servers likely constitutes infringement. But personally owned PDF copies of books ingested by local large language models should present no issues as no data leaves the client computer.

Local LLM Book Summarizer sidesteps these issues by running entirely on the client computer through a local LLM and "chunking" books into manageable pieces that can be summarized and then synthesized together.

## Project Workflow

### Overview

This project processes full-length books (PDFs) into structured, research-grade summaries using a local LLM. It preserves argument structure, page references, and historiographical content rather than producing generic summaries.

---

### Pipeline

#### 1. Input

- OCR’d PDF of a book  
- Assumes text is extractable (no image-only scans)

---

#### 2. Text Extraction

- Extract text page by page using PyMuPDF  
- Preserve:
  - Page numbers  
  - Layout blocks (paragraphs, headings)  

Output:

```
Page → text blocks with metadata
```

---

#### 3. Structural Segmentation

Chapter Detection
- Prefer PDF Table of Contents (bookmarks)  
- Fallback: regex detection (e.g., “Chapter 1”, “Introduction”)  

Section Detection
- Use layout features:
  - Font size  
  - Block length  
  - Formatting patterns  

Output:

```
Book → Chapters → Sections
```

---

#### 4. Chunking

- Split sections into chunks based on token limits  
- Maintain structure:
  - Chapter  
  - Section  
  - Page range  

Output format (JSONL):

```json
{
  "chapter": "Chapter 3",
  "section": "The Dawes Plan",
  "start_page": 145,
  "end_page": 159,
  "text": "..."
}
```

---

#### 5. Chunk-Level Analysis

Each chunk is processed by a local LLM using a fixed schema:

- Main claim  
- Evidence  
- Key concepts  
- Examples/cases  
- Historiographical intervention  
- Method/source base  
- Page references  
- Questions/weaknesses  

---

#### 6. Chapter Synthesis

- Combine chunk outputs into a coherent chapter argument
- Focus on:
  - Argument progression  
  - Evidence structure  
  - Role within the book  

---

#### 7. Book-Level Synthesis

Generate a structured analytical summary:

- One-sentence thesis  
- Full argument  
- Chapter breakdown  
- Historiographical contribution  
- Methods and sources  
- Strengths and weaknesses

---

#### 8. Critical Pass

Second LLM pass to evaluate:

- Assumptions  
- Silences  
- Limitations  
- Historiographical stakes  

---

### Output

- Structured summaries (chunk, chapter, book)  
- Page-referenced analysis  
- Research-oriented interpretation  
- Searchable text corpus (optional)  

---

### Design Principles

- Preserve argument structure, not just content  
- Maintain page-level traceability
- Prioritize historiographical analysis
- Use LLMs as analytical assistants, not replacements for reading  

---

### Tech Stack (planned)

- Python  
- PyMuPDF (PDF extraction)  
- Local LLM (via LM Studio or API)  
- Possible: vector database (FAISS or similar)  

---

### Use Case

Designed for historians and researchers who need:

- Rapid orientation in large texts  
- Structured analytical summaries  
- Integration of books into ongoing research projects