from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT
from ebooklib.epub import EpubNav, Link

BLOCK_TAGS = [
    "p", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "td", "th", "figcaption", "dt", "dd",
]


def load_epub_paragraphs(path):
    """Parse every document item and collect translatable block-level units.

    Nested candidates (e.g. a <p> inside a <td> that is itself a candidate) are
    skipped so the same text isn't collected twice; the outer block is translated
    as a whole. Inline markup (bold/italic/links) inside a translated block is
    replaced with plain text - this is a known MVP limitation.

    Auto-generated navigation documents (EpubNav) are skipped: ebooklib
    regenerates their content from `book.toc` on write, so any edit made
    directly to their HTML would be silently discarded anyway. Chapter
    titles in the TOC/navigation therefore stay in the source language.
    """
    book = epub.read_epub(path)
    items = [i for i in book.get_items_of_type(ITEM_DOCUMENT) if not isinstance(i, EpubNav)]
    soups = {}
    units = []
    for item in items:
        soup = BeautifulSoup(item.get_content(), "html.parser")
        soups[item.get_id()] = (item, soup)
        candidates = soup.find_all(BLOCK_TAGS)
        candidate_ids = set(id(t) for t in candidates)
        for tag in candidates:
            if any(id(parent) in candidate_ids for parent in tag.parents):
                continue
            text = tag.get_text().strip()
            if text:
                units.append({"item_id": item.get_id(), "tag": tag, "text": text})
    return book, soups, units


def set_unit_text(unit, translated_text):
    tag = unit["tag"]
    tag.clear()
    tag.append(translated_text)


def _fix_toc_uids(toc, counter):
    """Work around an ebooklib quirk: when a book's TOC is parsed from an
    EPUB3 nav.xhtml (rather than a legacy toc.ncx), Link entries come back
    with uid=None, which crashes epub.write_epub(). Backfill a uid so the
    TOC round-trips instead of blowing up the whole export."""
    fixed = []
    for entry in toc:
        if isinstance(entry, tuple):
            section, children = entry
            fixed.append((section, _fix_toc_uids(children, counter)))
        else:
            if isinstance(entry, Link) and not entry.uid:
                counter[0] += 1
                entry.uid = f"toc_{counter[0]}"
            fixed.append(entry)
    return fixed


def write_epub(book, soups, output_path):
    for item, soup in soups.values():
        item.set_content(str(soup).encode("utf-8"))
    book.toc = _fix_toc_uids(list(book.toc), [0])
    epub.write_epub(output_path, book)
