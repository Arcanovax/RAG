from .chunking import Chunking
from .retrieving import Retrieving
from .indexing import Indexing
from pathlib import Path
from enum import Enum
from .utils.model import StudentSearchResults, MinimalSearchResults, MinimalSource
import json

class dataset(Enum):
    CODE = "code"
    DOCS = "docs"


def main():
    raw = Path("data/raw")

    max_chunk_size = 2000
    k = 10
    dataset_type = dataset.DOCS
    chunks_file = Path("data/processed/chunks.json")
    bm25s_path = Path("data/processed/bm25_index")

    all_chunks = Chunking(
        raw,
        max_chunk_size,
        chunks_file,
        dataset_type,
    ).get_all_chunks()
    Indexing(bm25s_path, all_chunks)

    questions = get_questions(Path("data/datasets_public/public/UnansweredQuestions/dataset_docs_public.json"))
    all = []
    for question in questions:
        print(question.get("question"))
        selected_chunks = Retrieving(bm25s_path, chunks_file, question.get("question"), k).get_selected_chunks()
        sources = []
        for chunk in selected_chunks:
            sources.append({
                    "file_path": chunk.get("file_path"),
                    "first_character_index": chunk.get("first_character_index"),
                    "last_character_index": chunk.get("last_character_index")
                })
        answer = {
            "question_id": question.get("question_id"),
            "question_str": question.get("question"),
            "retrieved_sources": sources
        }
        all.append(answer)
    save_all_answer(all, k)


def save_all_answer(all, k):
    try:
        data = {
            "search_results": all,
            "k": k
        }
        with (open("result.json", "w")as file):
            file.write(json.dumps(data, indent=2))
    except Exception:
        raise (ValueError("Cannot write"))


def get_questions(file):
    try:
        with (open(file, "r")as file):
            data = file.read()
            data = json.loads(data)
            return data.get("rag_questions")
    except Exception:
        raise (ValueError(f"Cannot write in {file}"))


if __name__ == "__main__":
    main()
