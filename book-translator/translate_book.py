#!/usr/bin/env python3
"""Translate a book (.txt or .epub) from one language to another using the OpenAI API."""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from booktranslator import epub_io, txt_io
from booktranslator.cache import TranslationCache
from booktranslator.chunking import make_batches
from booktranslator.translator import translate_batch


def detect_format(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".epub":
        return "epub"
    if ext == ".txt":
        return "txt"
    raise ValueError(f"Unsupported input format '{ext}' (use .txt or .epub)")


def default_output_path(input_path, target_lang):
    base, ext = os.path.splitext(input_path)
    return f"{base}.{target_lang}{ext}"


def build_arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the source book (.txt or .epub)")
    parser.add_argument("output", nargs="?", help="Output path (default: <input>.<target-lang>.<ext>)")
    parser.add_argument("--source-lang", default="en", help="Source language code (default: en)")
    parser.add_argument("--target-lang", default="cs", help="Target language code (default: cs)")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use (default: gpt-4o-mini)")
    parser.add_argument("--max-chars", type=int, default=4000, help="Max characters per API batch")
    parser.add_argument("--max-paragraphs", type=int, default=40, help="Max paragraphs per API batch")
    parser.add_argument("--concurrency", type=int, default=4, help="Parallel API requests (default: 4)")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--cache", default=None, help="Cache file path (default: <input>.cache.json)")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching / resume support")
    parser.add_argument("--dry-run", action="store_true", help="Only report paragraph/char counts; no API calls")
    parser.add_argument("--api-key", default=None, help="OpenAI API key (default: OPENAI_API_KEY env var)")
    return parser


def load_source(input_path, fmt):
    if fmt == "txt":
        paragraphs = txt_io.load_txt_paragraphs(input_path)
        return paragraphs, None
    book, soups, units = epub_io.load_epub_paragraphs(input_path)
    paragraphs = [u["text"] for u in units]
    return paragraphs, (book, soups, units)


def write_output(fmt, output_path, translated, epub_state):
    if fmt == "txt":
        txt_io.write_txt(translated, output_path)
        return
    book, soups, units = epub_state
    for unit, text in zip(units, translated):
        epub_io.set_unit_text(unit, text)
    epub_io.write_epub(book, soups, output_path)


def main():
    args = build_arg_parser().parse_args()

    try:
        fmt = detect_format(args.input)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or default_output_path(args.input, args.target_lang)

    paragraphs, epub_state = load_source(args.input, fmt)
    total_chars = sum(len(p) for p in paragraphs)
    print(f"[book-translator] {len(paragraphs)} paragraphs, {total_chars} characters to translate.")

    if args.dry_run:
        print("[book-translator] Dry run: no API calls made.")
        return

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: no OpenAI API key. Set OPENAI_API_KEY or pass --api-key.", file=sys.stderr)
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    cache = None
    if not args.no_cache:
        cache_path = args.cache or (args.input + ".cache.json")
        cache = TranslationCache(cache_path)

    translated = [None] * len(paragraphs)
    pending_indices = []
    for i, p in enumerate(paragraphs):
        cached = cache.get(p, args.model, args.source_lang, args.target_lang) if cache else None
        if cached is not None:
            translated[i] = cached
        else:
            pending_indices.append(i)

    print(
        f"[book-translator] {len(paragraphs) - len(pending_indices)} paragraphs from cache, "
        f"{len(pending_indices)} to translate."
    )

    pending_texts = [paragraphs[i] for i in pending_indices]
    batches = make_batches(pending_texts, args.max_chars, args.max_paragraphs)

    index_batches = []
    cursor = 0
    for batch in batches:
        idxs = pending_indices[cursor : cursor + len(batch)]
        cursor += len(batch)
        index_batches.append((idxs, batch))

    def worker(idxs, texts):
        results = translate_batch(
            client, texts, args.model, args.source_lang, args.target_lang, args.temperature
        )
        return idxs, texts, results

    done_batches = 0
    failed = False
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker, idxs, texts) for idxs, texts in index_batches]
        for future in as_completed(futures):
            try:
                idxs, texts, results = future.result()
            except Exception as e:
                print(f"[book-translator] batch failed: {e}", file=sys.stderr)
                failed = True
                continue
            for i, src, tr in zip(idxs, texts, results):
                translated[i] = tr
                if cache:
                    cache.set(src, args.model, args.source_lang, args.target_lang, tr)
            done_batches += 1
            translated_count = sum(1 for t in translated if t is not None)
            print(
                f"[book-translator] batch {done_batches}/{len(index_batches)} done "
                f"({translated_count}/{len(paragraphs)} paragraphs)"
            )
            if cache:
                cache.save()

    if failed or any(t is None for t in translated):
        print(
            "Error: some paragraphs failed to translate. Re-run the same command to "
            "resume from the cache.",
            file=sys.stderr,
        )
        sys.exit(1)

    write_output(fmt, output_path, translated, epub_state)
    print(f"[book-translator] Done. Output written to {output_path}")


if __name__ == "__main__":
    main()
