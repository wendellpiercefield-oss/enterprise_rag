import re

MAX_CHARS = 1500


def chunk_text(text: str):
    # Split by logical sections first (paragraphs, steps)
    sections = re.split(r'\n\s*\n', text)

    chunks = []
    current = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # If section is too big, split further
        if len(section) > MAX_CHARS:
            parts = [section[i:i+MAX_CHARS] for i in range(0, len(section), MAX_CHARS)]
        else:
            parts = [section]

        for part in parts:
            if len(current) + len(part) < MAX_CHARS:
                current += "\n\n" + part
            else:
                if current:
                    chunks.append(current.strip())
                current = part

    if current:
        chunks.append(current.strip())

    return chunks