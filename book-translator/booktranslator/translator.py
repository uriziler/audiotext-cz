import json
import random
import time

from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, RateLimitError

SYSTEM_PROMPT = (
    "You are a professional literary translator. Translate the given numbered text "
    "segments from {source} to {target}. Keep exactly the same number of segments, "
    "in the same order, preserving meaning, tone and paragraph structure with natural "
    "{target} prose. Do not add, remove, merge or split segments, and do not add any "
    "commentary. Return ONLY a JSON object of the form "
    '{{"translations": ["...", ...]}} with exactly {n} strings, in the same order as '
    "the input segments."
)

RETRYABLE_ERRORS = (RateLimitError, APIConnectionError, APITimeoutError)


class TranslationError(Exception):
    pass


def _call_api(client, paragraphs, model, source_lang, target_lang, temperature):
    system = SYSTEM_PROMPT.format(source=source_lang, target=target_lang, n=len(paragraphs))
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"segments": paragraphs}, ensure_ascii=False)},
        ],
    )
    content = response.choices[0].message.content
    data = json.loads(content)
    translations = data["translations"]
    if not isinstance(translations, list) or len(translations) != len(paragraphs):
        raise TranslationError(
            f"expected {len(paragraphs)} translations, got "
            f"{len(translations) if isinstance(translations, list) else type(translations)}"
        )
    return translations


def translate_batch(client, paragraphs, model, source_lang, target_lang, temperature=0.3, max_retries=5):
    """Translate a batch of paragraphs in one API call. On malformed output the
    batch is split in half and retried recursively, down to single paragraphs,
    so one bad response doesn't sink the whole batch."""
    if not paragraphs:
        return []

    last_err = None
    for attempt in range(max_retries):
        try:
            return _call_api(client, paragraphs, model, source_lang, target_lang, temperature)
        except RETRYABLE_ERRORS as e:
            last_err = e
            time.sleep(min(60, (2 ** attempt) + random.random()))
        except (TranslationError, json.JSONDecodeError, KeyError, APIStatusError, APIError) as e:
            last_err = e
            if len(paragraphs) > 1:
                mid = len(paragraphs) // 2
                left = translate_batch(
                    client, paragraphs[:mid], model, source_lang, target_lang, temperature, max_retries
                )
                right = translate_batch(
                    client, paragraphs[mid:], model, source_lang, target_lang, temperature, max_retries
                )
                return left + right
            time.sleep(min(30, (2 ** attempt) + random.random()))

    raise TranslationError(f"failed to translate batch of {len(paragraphs)} after {max_retries} attempts: {last_err}")
