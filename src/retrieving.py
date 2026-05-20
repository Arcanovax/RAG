import bm25s
import json
from pathlib import Path
import chromadb
import spacy
import Stemmer


class Retrieving():
    CACHE_PATH = Path("./cache/expand_query_cache.json")

    def __init__(self, bm25s_path, chunks_file: Path, k, is_hybrid, is_expand):
        self.chunks_file = chunks_file
        self.bm25s_path = bm25s_path
        self.is_hybrid = is_hybrid
        self.is_expand = is_expand
        if is_expand:
            self.nlp = spacy.load("en_core_web_lg")
        self.k = k
        self.get_chunks()

    def retrieve(self, question: str):
        ret_loaded = bm25s.BM25(k1=1.7).load(self.bm25s_path, load_corpus=True)
        if self.is_expand:
            expand_question = self.expand_query(question)
            query_tokens = bm25s.tokenize(expand_question)
        else:
            query_tokens = bm25s.tokenize(question)
        if not self.is_hybrid:
            docs, scores = ret_loaded.retrieve(query_tokens, k=self.k)
            return [self.chunks[i] for i in docs[0]]
        else:
            k_pool = max(self.k * 10, 50)
            client = chromadb.PersistentClient(path="data/processed/chroma_db")
            if not self._is_semantic_valid(client):
                raise ValueError("Cannot use the --hybrid flag ont this data")
            chroma_chunks = client.get_collection(name="Chunks")
            results = chroma_chunks.query(
                query_texts=question,
                n_results=k_pool,
            )
            docs, scores = ret_loaded.retrieve(query_tokens, k=k_pool)
            chroma_ids = [int(i) for i in results["ids"][0]]
            bm25_ids = list(docs[0])
            scores: dict[str, float] = {}

            ranked_lists = [
                (chroma_ids, 0.85),
                (bm25_ids, 1.15),
            ]

            for doc_list, weight in ranked_lists:
                for rank, doc_id in enumerate(doc_list):
                    score = weight * (1.0 / (self.k + rank + 1))
                    scores[doc_id] = scores.get(doc_id, 0.0) + score

            fused_ids = [doc_id for doc_id, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)][:self.k]
            return [self.chunks[int(i)] for i in fused_ids]




    def _is_semantic_valid(self, client: chromadb.ClientAPI):
        for collection in client.list_collections():
            if collection.name == "Chunks":
                return True
        return False

    def get_chunks(self):
        try:
            with (open(self.chunks_file, "r")as file):
                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError("The dataset is not indexed, use index before"))

    def expand_query(self, question):
        cache = {}
        if self.CACHE_PATH.exists():
            cache = json.loads(self.CACHE_PATH.read_text())

        if question in cache:
            return cache[question]

        expanded = self.expand(question)

        cache[question] = expanded
        self.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
        return expanded


    def expand(self, question):
        doc = self.nlp(question)
        keywords = [token.lemma_ for token in doc
                    if not token.is_stop and token.is_alpha]

        similar_terms = []
        for token in doc:
            if not token.is_stop and token.has_vector and token.vocab.vectors.shape[0] > 0:
                similar = token.vocab.vectors.most_similar(
                    token.vector.reshape(1, -1), n=3
                )
                similar_terms += [token.vocab.strings[i] for i in similar[0][0]]

        expanded = f"{question} {' '.join(keywords)} {' '.join(similar_terms)}"
        return expanded
