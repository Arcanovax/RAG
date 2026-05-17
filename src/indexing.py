import bm25s
import chromadb

class Indexing:
    def __init__(self, save_path, all_chunks):
        self.save_path = save_path
        self.all_chunks = all_chunks
        self.save_for_retriever()

    def save_for_retriever(self):
        corpus = []
        chroma_ids = []
        chroma_metadatas = []
        chroma_documents = []
        for id, chunk in enumerate(self.all_chunks):
            corpus.append(f"{chunk['file_path']}   {chunk['content']}")
            chroma_documents.append(chunk['content'])
            chroma_ids.append(f"id{id}")
            chroma_metadatas.append({"source": chunk['file_path']})
        retriever = bm25s.BM25()
        corpus_tokens = bm25s.tokenize(corpus)
        retriever.index(corpus_tokens)
        retriever.save(self.save_path)
        self.chroma_save(chroma_documents, chroma_ids, chroma_metadatas)
        
    def chroma_save(self,chroma_documents, chroma_ids, chroma_metadatas):
        client = chromadb.PersistentClient(path="./chroma_db")
        chroma_chunks = client.create_collection(name="Chunks")
        chroma_chunks.add(
            documents = chroma_documents,
            metadatas = chroma_metadatas,
            ids = chroma_ids
        )