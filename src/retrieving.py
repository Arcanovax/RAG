import bm25s
import json
from pathlib import Path


class Retrieving():
    def __init__(self, bm25s_path, chunks_file: Path, question, k):
        self.chunks_file = chunks_file
        self.question = question
        self.get_chunks()

        ret_loaded = bm25s.BM25.load(bm25s_path, load_corpus=True)
        query_tokens = bm25s.tokenize(question)
        docs, scores = ret_loaded.retrieve(query_tokens, k=k)
        self.selected_chunks = [self.chunks[i] for i in docs[0]]

    def get_selected_chunks(self):
        return self.selected_chunks

    def get_chunks(self):
        try:
            with (open(self.chunks_file, "r")as file):
                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError(f"Cannot read {self.chunks_file}"))

