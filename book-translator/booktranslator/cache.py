import hashlib
import json
import os


class TranslationCache:
    """JSON-backed cache so an interrupted run can resume without re-paying for
    already-translated paragraphs."""

    def __init__(self, path):
        self.path = path
        self.data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    @staticmethod
    def _key(text, model, source_lang, target_lang):
        h = hashlib.sha256()
        h.update(f"{model}|{source_lang}|{target_lang}|{text}".encode("utf-8"))
        return h.hexdigest()

    def get(self, text, model, source_lang, target_lang):
        return self.data.get(self._key(text, model, source_lang, target_lang))

    def set(self, text, model, source_lang, target_lang, translation):
        self.data[self._key(text, model, source_lang, target_lang)] = translation

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False)
        os.replace(tmp, self.path)
