from pathlib import Path
import bm25s
import json
import os

def main():
    raw = "data/raw"
    processed = "data/processed"
    file = "chunks.json"
    question = "What HTTP endpoint is used to dynamically load a LoRA adapter in vLLM?"
    Chunking(raw, 2000, processed, file)
    Indexing(processed, file, question)


class Indexing():
    def __init__(self, processed: str, file: str, question: str):
        self.folder_processed = processed
        self.json_chunks = file
        self.question = question
        self.get_chunks()
        corpus = [chunk.get("content") for chunk in self.chunks]
        corpus_tokens = bm25s.tokenize(corpus)
        self.retriever = bm25s.BM25(corpus=corpus)
        self.retriever.index(corpus_tokens)

        query_tokens = bm25s.tokenize(question)
        docs, scores = self.retriever.retrieve(query_tokens, k=2)
        print(f"Best result (score: {scores[0][0]:.2f})")
        result = docs[0][0]
        chunk = self.find_chunk(result)
        print(chunk)

    def find_chunk(self, content):
        for chunk in self.chunks:
            if content == chunk.get("content"):
                return chunk

    def get_chunks(self):
        chunks_file = f"{self.folder_processed}/{self.json_chunks}"
        try:
            with (open(chunks_file, "r")as file):

                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError(f"Cannot write in {self.json_chunks}"))


class Chunking():
    def __init__(self, folder_raw: str, max_chunk_size: int, processed: str, file: str):
        self.allowed_text = [".md", ".txt", ".toml"]
        self.allowed_code = [".py"]
        self.folder_raw = folder_raw
        self.max_chunk_size = max_chunk_size
        self.folder_processed = processed
        self.json_chunks = file
        self.find_allowed_files_paths(self.allowed_text)
        self.chunking_files_paths()

    def find_allowed_files_paths(self, allowed):
        folder = Path(self.folder_raw)
        self.files_paths = []
        for ext in allowed:
            self.files_paths += (list(folder.rglob(f"*{ext}")))

    def save_chunks(self, chunks: list):
        chunks_file = f"{self.folder_processed}/{self.json_chunks}"
        try:
            with (open(chunks_file, "w")as file):
                file.write(json.dumps(chunks, indent=2))
        except Exception:
            raise (ValueError(f"Cannot write in {self.json_chunks}"))

    def create_chunks(self, file_path) -> dict:
        data = file_path.read()
        chunk_size = self.max_chunk_size
        total_size = len(data)
        chunks = []
        for i in range(0, total_size, chunk_size):
            chunks.append({
                    "file_path": file_path.name,
                    "content": data[i:i + chunk_size],
                    "first_character_index": i,
                    "last_character_index": i + chunk_size
                })
        return chunks

    def chunking_files_paths(self):
        os.makedirs(self.folder_processed, exist_ok=True)
        chunks = []
        for file_path in self.files_paths:
            with (open(file_path, "r") as file):
                chunks += self.create_chunks(file)
        self.save_chunks(chunks)

if __name__ == "__main__":
    main()


