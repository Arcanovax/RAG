import bm25s
import json
from pathlib import Path
import chromadb
from functools import lru_cache


class Retrieving():
    CACHE_PATH = Path("./cache/expand_query_cache.json")
    def __init__(self, bm25s_path, chunks_file: Path, question, k, is_hybrid, nlp):
        self.chunks_file = chunks_file
        self.question = question
        self.get_chunks()
        if nlp is not None:
            question = self.expand_query(question, nlp)
        ret_loaded = bm25s.BM25.load(bm25s_path, load_corpus=True)
        query_tokens = bm25s.tokenize(question)
        docs, scores = ret_loaded.retrieve(query_tokens, k=k)
        if not is_hybrid:
            self.selected_chunks = [self.chunks[i] for i in docs[0]]
        else:
                client = chromadb.PersistentClient(path="data/processed/chroma_db")
                if not self.is_semantic_valid(client):
                    raise ValueError("Cannot use the --hybrid flag ont this data")
                chroma_chunks = client.get_collection(name="Chunks")
                results = chroma_chunks.query(
                    query_texts=self.question,
                    n_results=k,
                )
                chroma_ids = [int(i) for i in results["ids"][0]]
                bm25_ids = list(docs[0])
                self.selected_chunks = [self.chunks[i] for i in bm25_ids[:8]+chroma_ids[:2]]


    def is_semantic_valid(self, client:chromadb.ClientAPI):
        for collection in client.list_collections():
            if collection.name == "Chunks":
                return True
        return False

    def get_selected_chunks(self):
        return self.selected_chunks

    def get_chunks(self):
        try:
            with (open(self.chunks_file, "r")as file):
                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError("The dataset is not indexed, use index before"))

    def expand_query(self, question, nlp):
        cache = {}
        if self.CACHE_PATH.exists():
            cache = json.loads(self.CACHE_PATH.read_text())

        if question in cache:
            return cache[question]

        expanded = self.expand(question, nlp)

        cache[question] = expanded
        self.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
        return expanded


    def expand(self, question, nlp):
        doc = nlp(question)
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
