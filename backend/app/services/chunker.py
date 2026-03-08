import re


def chunk_text(text, chunk_size=1200, overlap=200):

    # normalize whitespace
    text = re.sub(r'\r', '', text)

    # split on headings and figures
    sections = re.split(
        r'\n(?=(Table|Figure|Disassembly|Assembly|Specifications|Dimensions))',
        text,
        flags=re.IGNORECASE
    )

    chunks = []
    current_chunk = ""

    for section in sections:

        if len(current_chunk) + len(section) < chunk_size:
            current_chunk += section
        else:
            chunks.append(current_chunk.strip())
            current_chunk = section

    if current_chunk:
        chunks.append(current_chunk.strip())

    # add overlap to preserve context
    final_chunks = []
    for i, chunk in enumerate(chunks):

        if i > 0:
            overlap_text = chunks[i-1][-overlap:]
            chunk = overlap_text + "\n" + chunk

        final_chunks.append(chunk)

    return final_chunks