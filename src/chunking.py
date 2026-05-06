from pathlib import Path
import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import re

class Chunking():
    def __init__(self, folder_raw: Path, max_chunk_size: int, chunks_file: Path, dataset_type):
        self.folder_raw = folder_raw
        self.chunks_file = chunks_file
        if dataset_type.value == "code":
            self.allowed_ext = [".py"]
            self.language = Language.PYTHON
        else:
            self.allowed_ext = [".md", ".txt", ".toml"]
            self.language = Language.MARKDOWN

        self.text_splitter = RecursiveCharacterTextSplitter.from_language(
            language=self.language,
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * 0.05),
            add_start_index=True
        )
        self.find_allowed_files_paths(self.allowed_ext)
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
        data = clean_text(data)
        texts = self.text_splitter.create_documents([data])
        chunks = []


        for text in texts:
            index = text.metadata.get("start_index")
            text = text.page_content
            last_index = index + len(text)
            chunks.append({
                "file_path": file_path.name,
                "content": text,
                "first_character_index": index,
                "last_character_index": last_index
            })
        return chunks

    def chunking_files_paths(self):
        os.makedirs(self.chunks_file.parent.name, exist_ok=True)
        chunks = []
        for file_path in self.files_paths:
            with (open(file_path, "r") as file):
                chunks += self.create_chunks(file)
        self.save_chunks(chunks)




def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zàâçéèêëîïôûùµvñ ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
