import re


def load_txt_paragraphs(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    raw_paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in raw_paragraphs if p.strip()]


def write_txt(paragraphs, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(paragraphs))
        f.write("\n")
