from .chunking import Chunking
from .indexing import Indexing
from pathlib import Path

def main():
    raw = Path("data/raw")
    chunks_file = Path("data/processed/chunks.json")
    max_chunk_size = 2000
    question = "What HTTP endpoint is used to dynamically load a LoRA adapter in vLLM?"

    Chunking(raw, max_chunk_size, chunks_file)
    Indexing(chunks_file, question)



if __name__ == "__main__":
    main()


