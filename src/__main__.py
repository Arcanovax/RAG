from .chunking import Chunking
from .indexing import Indexing
from pathlib import Path
from enum import Enum
import json

class dataset(Enum):
    CODE = "code"
    DOCS = "docs"


def main():
    raw = Path("data/raw")
    chunks_file = Path("data/processed/chunks.json")
    max_chunk_size = 2000
    dataset_type = dataset.DOCS
    Chunking(raw, max_chunk_size, chunks_file, dataset_type)

    questions = get_questions(Path("data/datasets_public/public/UnansweredQuestions/dataset_docs_public.json"))
    all = []
    for question in questions:
        print(question.get("question"))
        indexing = Indexing(chunks_file, question.get("question"))
        chunk = indexing.get_chunk()
        answer = {
            "question_id": question.get("question_id"),
            "question_str": question.get("question"),
            "retrieved_sources": [
                {
                    "file_path": chunk.get("file_path"),
                    "first_character_index": chunk.get("first_character_index"),
                    "last_character_index": chunk.get("last_character_index")
                }]
        }
        all.append(answer)
    save_all(all)

def save_all(all):
    try:
        data = {
            "search_results": all,
            "k": 10
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
        raise (ValueError(f"Cannot write in {self.json_chunks}"))


if __name__ == "__main__":
    main()


