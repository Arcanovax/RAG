import bm25s
import chromadb
from tqdm import tqdm
import shutil
from pathlib import Path

class Indexing:
    def __init__(self, save_path, all_chunks, dataset_type, process_path):
        self.save_path = save_path
        self.all_chunks = all_chunks
        self.dataset_type = dataset_type
        self.process_path = process_path
        self.chroma_path = Path(f"{self.process_path}/chroma_db")
        if self.chroma_path.exists():
            shutil.rmtree(self.chroma_path)
        self.save_for_retriever()
        if dataset_type == "docs":
            print("Saving for semantic search...")
            self.chroma_save()
            print("Saved for semantic search")

        print(f"Ingestion complete! Indices saved under {self.process_path}")

    def save_for_retriever(self):
        corpus = []
        self.chroma_ids = []
        self.chroma_metadatas = []
        self.chroma_documents = []
        for id, chunk in enumerate(self.all_chunks):
            corpus.append(f"{chunk['file_path']}   {chunk['content']}")
            self.chroma_documents.append(chunk['content'])
            self.chroma_ids.append(str(id))
            self.chroma_metadatas.append({"source": chunk['file_path']})
        retriever = bm25s.BM25()
        corpus_tokens = bm25s.tokenize(corpus)
        retriever.index(corpus_tokens)
        retriever.save(self.save_path)

    def chroma_save(self):
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        chroma_chunks = self.client.get_or_create_collection(name="Chunks")
        chroma_chunks.add(
            documents=self.chroma_documents,
            metadatas=self.chroma_metadatas,
            ids=self.chroma_ids
        )
