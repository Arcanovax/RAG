import bm25s
import json
from pathlib import Path


class Indexing():
    def __init__(self, chunks_file: Path, question):
        self.chunks_file = chunks_file
        self.question = question
        self.get_chunks()

        ret_loaded = bm25s.BM25.load("data/processed/bm25_index", load_corpus=True)
        query_tokens = bm25s.tokenize(question)
        docs, scores = ret_loaded.retrieve(query_tokens, k=10)
        print(f"Best result (score: {scores[0][0]:.2f})")
        result = docs[0][0]
        self.chunk = self.chunks[result]

    def get_chunk(self):
        return self.chunk

    def get_chunks(self):
        try:
            with (open(self.chunks_file, "r")as file):
                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError(f"Cannot write in {self.json_chunks}"))()

