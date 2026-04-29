def chunk_summary_prompt(chunk):
    return f"""
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


def batch_synthesis_prompt(combined):
    return f"""
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


def final_summary_prompt(combined):
    return f"""
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


def verification_prompt(final_summary, combined):
    return f"""
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