import bm25s


class Indexing:
    def __init__(self, save_path, all_chunks):
        self.save_path = save_path
        self.all_chunks = all_chunks
        self.save_for_retriever()

    def save_for_retriever(self):
        corpus = []
        for chunk in self.all_chunks:
            corpus.append(f"{chunk['file_path']}   {chunk['content']}")
        retriever = bm25s.BM25()
        corpus_tokens = bm25s.tokenize(corpus)
        retriever.index(corpus_tokens)
        retriever.save(self.save_path)
