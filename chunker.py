def estimate_tokens(text):
    return int(len(text.split()) * 1.3)

def chunk_pages(pages, max_tokens=2000):
    chunks = []
    current_text = []
    current_pages = []
    current_tokens = 0

    for page in pages:
        text = page["text"]
        tokens = estimate_tokens(text)

        if current_tokens + tokens > max_tokens and current_text:
            chunks.append({
                "text": "\n\n".join(current_text),
                "start_page": min(current_pages),
                "end_page": max(current_pages)
            })
            current_text = []
            current_pages = []
            current_tokens = 0

        current_text.append(text)
        current_pages.append(page["page_number"])
        current_tokens += tokens

    if current_text:
        chunks.append({
            "text": "\n\n".join(current_text),
            "start_page": min(current_pages),
            "end_page": max(current_pages)
        })

    return chunks