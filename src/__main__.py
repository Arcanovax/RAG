from .chunking import Chunking
from .retrieving import Retrieving
from .indexing import Indexing
from .evaluating import Evaluating
from pathlib import Path
from enum import Enum
from .utils.model import (StudentSearchResults,
                          MinimalSearchResults,
                          MinimalSource)
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
    search_results = Path("data/output/search_results/dataset_docs_public.json")
    questions_path = Path("data/datasets_public/public/UnansweredQuestions/dataset_docs_public.json")
    answered_path = Path("data/datasets_public/public/AnsweredQuestions/dataset_docs_public.json")

    all_chunks = Chunking(
        raw,
        max_chunk_size,
        chunks_file,
        dataset_type,
    ).get_all_chunks()
    Indexing(bm25s_path, all_chunks)

    questions = get_questions(questions_path)
    all = []
    for question in questions:
        print(question.get("question"))
        selected_chunks = Retrieving(bm25s_path, chunks_file, question.get("question"), k).get_selected_chunks()
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        answer = {
            "question_id": question.get("question_id"),
            "question": question.get("question"),
            "retrieved_sources": sources
        }
        all.append(MinimalSearchResults(**answer))
    save_all_answer(search_results, all, k)
    save_for_moulinette(all, k)
    Evaluating(search_results, answered_path)


def save_for_moulinette(results, k):
    try:
        all = []
        for result in results:
            sources = []
            for chunk in result.retrieved_sources:
                sources.append({
                        "file_path": chunk.file_path,
                        "first_character_index": chunk.first_character_index,
                        "last_character_index": chunk.last_character_index})
            answer = {
                "question_id": result.question_id,
                "question_str": result.question,
                "retrieved_sources": sources
            }
            all.append(answer)
        data = {
            "search_results": all,
            "k": k
        }
        with (open("result.json", "w")as file):
            file.write(json.dumps(data, indent=2))
    except Exception:
        raise (ValueError("Cannot write"))


def save_all_answer(path, all, k):
    # try:
        result = StudentSearchResults(
            search_results=all,
            k=k
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as file:
            file.write(result.model_dump_json(indent=2))
    # except Exception:
    #     raise (ValueError("Cannot write"))


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
