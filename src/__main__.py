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
import fire



class Core:
    def __init__(
        self,
        k=10,
        dataset_type="docs",
        process_path=Path("data/processed"),
        output_path=Path("data/output"),
        chunks_file="chunks.json",
        bm25s_folder="bm25_index",
        search_results=Path("data/output/search_results/dataset_docs_public.json"),
        questions_path=Path("data/datasets_public/public/UnansweredQuestions/dataset_docs_public.json"),
        answered_path=Path("data/datasets_public/public/AnsweredQuestions/dataset_docs_public.json")
    ):
        self.k = k
        self.dataset = Path("data/raw")
        self.dataset_type = dataset_type
        self.search_results = search_results
        self.questions_path = questions_path
        self.answered_path = answered_path
        self.process_path = process_path
        self.chunks_path = process_path / chunks_file
        self.bm25s_path = process_path / bm25s_folder

    def index(self, max_chunk_size=2000, dataset=None, dataset_type="docs"):
        print(dataset_type)
        if dataset is None:
            dataset_path = self.dataset
        else:
            dataset_path = Path(dataset)

        self.all_chunks = Chunking(
            dataset_path,
            max_chunk_size,
            self.chunks_path,
            dataset_type
        ).get_all_chunks()

        if len(self.all_chunks) == 0:
            raise (ValueError("No files found"))
        Indexing(self.bm25s_path, self.all_chunks)
        print(f"Ingestion complete! Indices saved under {self.process_path}")

    def answer(self):
        print("search")
        pass

    def search_dataset(self, dataset_path, k, save_directory=None):
        questions = get_questions(Path(dataset_path))
        all = []
        for question in questions:
            print(question.get("question"))
            selected_chunks = Retrieving(self.bm25s_path, self.chunks_path, question.get("question"), k).get_selected_chunks()
            sources = []
            for chunk in selected_chunks:
                sources.append(MinimalSource(**chunk))
            answer = {
                "question_id": question.get("question_id"),
                "question": question.get("question"),
                "retrieved_sources": sources
            }
            all.append(MinimalSearchResults(**answer))
        self.save_all_answer(save_directory, all, k)
        save_for_moulinette(all, k)




    def search(self, query, k=5):
        print(query)
        selected_chunks = Retrieving(self.bm25s_path,
                                     self.chunks_file,
                                     query, k).get_selected_chunks()
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        print(sources)


    def answer_dataset(self):
        pass

    def evaluate(self):
        pass

    def save_all_answer(self, save_directory, all, k):
        if save_directory is None:
            save_path = self.search_results
        else:
            save_path = Path(save_directory) / "dataset_docs_public.json"
        result = StudentSearchResults(
            search_results=all,
            k=k
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as file:
            file.write(result.model_dump_json(indent=2))



def main():
    fire.Fire(Core)





    # questions = get_questions(questions_path)
    # all = []
    # for question in questions:
    #     print(question.get("question"))
    #     selected_chunks = Retrieving(bm25s_path, chunks_file, question.get("question"), k).get_selected_chunks()
    #     sources = []
    #     for chunk in selected_chunks:
    #         sources.append(MinimalSource(**chunk))
    #     answer = {
    #         "question_id": question.get("question_id"),
    #         "question": question.get("question"),
    #         "retrieved_sources": sources
    #     }
    #     all.append(MinimalSearchResults(**answer))
    # save_all_answer(search_results, all, k)
    # save_for_moulinette(all, k)
    # Evaluating(search_results, answered_path)


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




def get_questions(file):
    try:
        with (open(file, "r")as file):
            data = file.read()
            data = json.loads(data)
            return data.get("rag_questions")
    except Exception:
        raise (ValueError("questions not found"))


if __name__ == "__main__":
    main()
