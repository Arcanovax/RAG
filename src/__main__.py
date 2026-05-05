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
    for question in questions:
        print(question.get("question"))
        indexing = Indexing(chunks_file, question.get("question"))
        chunk = indexing.get_chunk()
        answer = {
            "question_id": question.get("question_id"),
            "retrieved_sources": [
                {
                    "file_path": chunk.get("file_path"),
                    "first_character_index": chunk.get("first_character_index"),
                    "last_character_index": chunk.get("last_character_index")
                }]
        }
        print(answer)

def save_answer(self, answer):
    try:
        with (open("result.json", "a")as file):
            file.write(json.dumps(answer, indent=2))
    except Exception:
        raise (ValueError(f"Cannot write in {self.chunks_file}"))


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


