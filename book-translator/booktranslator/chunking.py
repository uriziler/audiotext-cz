def make_batches(paragraphs, max_chars=4000, max_paragraphs=40):
    """Group paragraphs into batches under a character/count budget, preserving order."""
    batches = []
    current = []
    current_chars = 0
    for p in paragraphs:
        p_len = len(p)
        if current and (current_chars + p_len > max_chars or len(current) >= max_paragraphs):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(p)
        current_chars += p_len
    if current:
        batches.append(current)
    return batches
