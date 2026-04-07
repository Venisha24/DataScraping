"""
chunking.py
-----------
Splits long text content into smaller chunks for downstream processing.
"""


def chunk_text(text: str, max_words: int = 150) -> list[str]:
    """
    Split text into chunks of roughly max_words words each.
    Tries to split at paragraph boundaries first, then falls back to word count.

    Args:
        text: The full text to split.
        max_words: Approximate maximum words per chunk.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_word_count = 0

    for para in paragraphs:
        word_count = len(para.split())

        # If a single paragraph exceeds max_words, split it by sentences
        if word_count > max_words:
            sentences = para.replace("? ", "?|").replace("! ", "!|").replace(". ", ".|").split("|")
            for sentence in sentences:
                s_words = len(sentence.split())
                if current_word_count + s_words > max_words and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_word_count = s_words
                else:
                    current_chunk.append(sentence)
                    current_word_count += s_words
        else:
            if current_word_count + word_count > max_words and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [para]
                current_word_count = word_count
            else:
                current_chunk.append(para)
                current_word_count += word_count

    # Append any remaining content
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
