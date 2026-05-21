import bm25s
import json
from pathlib import Path
import chromadb
import spacy
from .utils.query_expander import Query_Expander


class Retrieving():
    def __init__(self, bm25s_path, chunks_file: Path, k, is_hybrid, is_expand):
        self.chunks_file = chunks_file
        self.bm25s_path = bm25s_path
        self.is_hybrid = is_hybrid
        self.is_expand = is_expand
        if is_expand:
            self.nlp = spacy.load("en_core_web_lg")
        self.k = k
        self.get_chunks()

    def retrieve(self, question: str):
        ret_loaded = bm25s.BM25(k1=1.7).load(self.bm25s_path, load_corpus=True)
        query_tokens = bm25s.tokenize(question)
        ranked_lists = []
        docs, scores = ret_loaded.retrieve(query_tokens, k=self.k)
        ranked_lists.append((list(docs[0]), 1.15))

        k_pool = max(self.k * 10, 50)

        if self.is_hybrid:
            client = chromadb.PersistentClient(path="data/processed/chroma_db")
            if not self._is_semantic_valid(client):
                raise ValueError("Cannot use the --hybrid flag ont these chunks, change the dataset type")
            chroma_chunks = client.get_collection(name="Chunks")
            results = chroma_chunks.query(
                query_texts=question,
                n_results=k_pool,
            )
            chroma_ids = [int(i) for i in results["ids"][0]]
            ranked_lists.append((chroma_ids, 0.85))

        if self.is_expand:
            expand_question = Query_Expander(self.nlp).expand_query(question)
            query_tokens = bm25s.tokenize(expand_question)
            docs, scores = ret_loaded.retrieve(query_tokens, k=k_pool)
            ranked_lists.append((list(docs[0]), 1.10))

        fused_ids = self._fusion_lists(ranked_lists)
        return [self.chunks[int(i)] for i in fused_ids]

    def _fusion_lists(self,
                      ranked_lists: list[tuple[list[str], float]]
                      ) -> list[str]:
        scores: dict[str, float] = {}
        for doc_list, weight in ranked_lists:
            for rank, doc_id in enumerate(doc_list):
                score = weight * (1.0 / (self.k + rank + 1))
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        fused_ids = [doc_id for doc_id, _ in sorted_docs]
        return fused_ids[:self.k]

    def _is_semantic_valid(self, client: chromadb.ClientAPI):
        for collection in client.list_collections():
            if collection.name == "Chunks":
                return True
        return False

    def get_chunks(self):
        try:
            with (open(self.chunks_file, "r")as file):
                data = file.read()
                self.chunks = json.loads(data)
        except Exception:
            raise (ValueError("The dataset is not indexed, use index before"))
