import bm25s
import json
from pathlib import Path


class Indexing():
    def __init__(self, chunks_file: Path, question):
        self.chunks_file = chunks_file
        self.question = question
        self.get_chunks()
        corpus = [chunk.get("content") for chunk in self.chunks]
        corpus_tokens = bm25s.tokenize(corpus)
        self.retriever = bm25s.BM25(corpus=corpus)
        self.retriever.index(corpus_tokens)

        query_tokens = bm25s.tokenize(question)
        docs, scores = self.retriever.retrieve(query_tokens, k=5)
        print(f"Best result (score: {scores[0][0]:.2f})")
        result = docs[0][0]
        self.chunk = self.find_chunk(result)

    def get_chunk(self):
        return self.chunk


    def find_chunk(self, content):
        for chunk in self.chunks:
            if content == chunk.get("content"):
                return chunk

    def get_chunks(self):
        try:
            with (open(self.chunks_file, "r")as file):
                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError(f"Cannot write in {self.json_chunks}"))

