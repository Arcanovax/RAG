import json
from pathlib import Path
import re


class Query_Expander():
    CACHE_PATH = Path("./.cache/expand_query_cache.json")

    def __init__(self, nlp):
        self.nlp = nlp

    def expand_query(self, question):
        cache = {}
        if self.CACHE_PATH.exists():
            cache = json.loads(self.CACHE_PATH.read_text())

        if question in cache:
            return cache[question]

        expanded = self.expand(question)
        cache[question] = expanded
        self.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False,
                                              indent=2))
        return expanded

    def expand(self, question):
        doc = self.nlp(question)
        keywords = self._get_keywords(doc)
        similar_words = self._get_similar_words(doc)
        code_keywords = self._get_code_keywords(doc)
        expanded = f"{question} {' '.join(keywords)} {' '.join(similar_words)}"
        expanded += f" {' '.join(code_keywords)}"
        return expanded

    def _get_keywords(self, doc):
        keywords = [token.lemma_ for token in doc
                    if not token.is_stop and token.is_alpha]
        return keywords

    def _get_similar_words(self, doc):
        similar_words = []
        for token in doc:
            if (not token.is_stop and token.is_alpha and token.has_vector
               and token.vocab.vectors.shape[0] > 0):
                similar = token.vocab.vectors.most_similar(
                    token.vector.reshape(1, -1), n=3
                )
                similar_words += [token.vocab.strings[i]
                                  for i in similar[0][0]]
        return similar_words

    def _get_code_keywords(self, doc):
        code_keywords = []
        for token in doc:
            if not token.is_stop:
                text = token.text
                if "_" in text or re.search(r'[a-z][A-Z]', text):
                    words = re.sub(r'[_.-]', ' ', text)
                    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', words)
                    code_keywords.append(words)
                    for part in words.split():
                        if (part.lower() not in self.nlp.Defaults.stop_words
                           and len(part) > 1):
                            code_keywords.append(part)
        return code_keywords
