from pathlib import Path
import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

class Chunking():
    def __init__(self, folder_raw: Path, max_chunk_size: int, chunks_file: Path):
        self.allowed_text = [".md", ".txt", ".toml"]
        self.allowed_code = [".py"]
        self.folder_raw = folder_raw
        self.chunks_file = chunks_file
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=max_chunk_size, chunk_overlap=0)
        self.find_allowed_files_paths(self.allowed_text)
        self.chunking_files_paths()


    def find_allowed_files_paths(self, allowed):
        self.files_paths = []
        for ext in allowed:
            self.files_paths += (list(self.folder_raw.rglob(f"*{ext}")))

    def save_chunks(self, chunks: list):
        try:
            with (open(self.chunks_file, "w")as file):
                file.write(json.dumps(chunks, indent=2))
        except Exception:
            raise (ValueError(f"Cannot write in {self.chunks_file}"))

    def create_chunks(self, file_path) -> dict:
        data = file_path.read()
        chunks = []

        texts = self.text_splitter.split_text(data)
        index = 0
        for text in texts:
            last_index = len(text)
            chunks.append({
                "file_path": file_path.name,
                "content": text,
                "first_character_index": index,
                "last_character_index": last_index
            })
            index = last_index + 1
        return chunks

    def chunking_files_paths(self):
        os.makedirs(self.chunks_file.parent.name, exist_ok=True)
        chunks = []
        for file_path in self.files_paths:
            with (open(file_path, "r") as file):
                chunks += self.create_chunks(file)
        self.save_chunks(chunks)
