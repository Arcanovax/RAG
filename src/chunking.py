from pathlib import Path
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import bm25s


class Chunking():
    def __init__(self, folder_raw: Path, max_chunk_size: int,
                 chunks_file: Path, dataset_type):
        self.folder_raw = folder_raw
        self.chunks_file = chunks_file
        overlap = 0.10
        if dataset_type.value == "code":
            self.allowed_ext = [".py"]
        else:
            self.allowed_ext = [".md", ".txt"]
        self.code_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * overlap),
            add_start_index=True
        )
        self.markdown_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * overlap),
            add_start_index=True
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * overlap),
            add_start_index=True
        )

        all_chunks = []
        for file_path in self._find_allowed_files_paths(self.allowed_ext):
            all_chunks += self.create_chunks_from_file(file_path)
        self.save_all_chunks(all_chunks)
        self.save_for_retriever(all_chunks)

    def _find_allowed_files_paths(self, allowed):
        files_paths = []
        for ext in allowed:
            files_paths += (list(self.folder_raw.rglob(f"*{ext}")))
        return files_paths

    def save_all_chunks(self, all_chunks: list):
        try:
            with (open(self.chunks_file, "w")as file):
                file.write(json.dumps(all_chunks, indent=2))
        except Exception:
            raise (ValueError(f"Cannot write in {self.chunks_file}"))

    def create_chunks_from_file(self, file_path) -> dict:
        data = file_path.read_text()
        if file_path.suffix == ".md":
            texts = self.markdown_splitter.create_documents([data])
        elif file_path.suffix == ".py":
            texts = self.code_splitter.create_documents([data])
        else:
            texts = self.text_splitter.create_documents([data])
        chunks = []
        for text in texts:
            chunk_text = text.page_content
            index = text.metadata.get("start_index")
            last_index = index + len(chunk_text)
            chunks.append({
                "file_path": str(file_path),
                "content": chunk_text,
                "first_character_index": index,
                "last_character_index": last_index
            })
        return chunks

    def save_for_retriever(self, all_chunks):
        corpus = []
        for chunk in all_chunks:
            corpus.append(f"{chunk['file_path']}   {chunk['content']}")
        retriever = bm25s.BM25()
        corpus_tokens = bm25s.tokenize(corpus)
        retriever.index(corpus_tokens)
        retriever.save("data/processed/bm25_index")
