"""Chunking utilities for dataset ingestion."""

from pathlib import Path
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language


class Chunking():
    """Create chunks from raw documents."""
    def __init__(self, folder_raw: Path, max_chunk_size: int,
                 chunks_file: Path, dataset_type):
        """Initialize chunking and write chunk file."""
        self.folder_raw = folder_raw
        self.chunks_file = chunks_file
        overlap = 0.20
        if dataset_type == "all":
            self.allowed_ext = [".py", ".md", ".txt"]
        elif dataset_type == "code":
            self.allowed_ext = [".py"]
        elif dataset_type == "docs":
            self.allowed_ext = [".md", ".txt"]
        else:
            raise ValueError("Unknow type of document")
        self.code_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * overlap),
            add_start_index=True,
        )
        self.markdown_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * overlap),
            add_start_index=True,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=int(max_chunk_size * overlap),
            add_start_index=True,
        )

        all_chunks = []
        for file_path in self._find_allowed_files_paths(self.allowed_ext):
            all_chunks += self.create_chunks_from_file(file_path)
        self.all_chunks = all_chunks
        save_all_chunks(self.chunks_file, all_chunks)

    def get_all_chunks(self):
        """Return all computed chunks."""
        return self.all_chunks

    def _find_allowed_files_paths(self, allowed):
        """Find files matching allowed extensions."""
        files_paths = []
        for ext in allowed:
            files_paths += (list(self.folder_raw.rglob(f"*{ext}")))
        return files_paths

    def create_chunks_from_file(self, file_path) -> dict:
        """Split a file into chunks with metadata."""
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


def save_all_chunks(chunks_file, all_chunks: list):
    """Persist chunks to disk as JSON."""
    chunks_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with (open(chunks_file, "w")as file):
            file.write(json.dumps(all_chunks, indent=2))
    except Exception:
        raise (ValueError(f"Cannot write in {chunks_file}"))


def get_chunks(chunks_file):
    """Load chunks from disk."""
    try:
        with (open(chunks_file, "r")as file):
            data = file.read()
            return json.loads(data)
    except Exception:
        raise (ValueError("The dataset is not indexed, use index before"))
