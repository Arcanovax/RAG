from .chunking import Chunking
from .retrieving import Retrieving
from .indexing import Indexing
from .evaluating import Evaluating
from .answering import Answering, Model
from pathlib import Path
from enum import Enum
from .utils.model import (StudentSearchResults,
                          MinimalSearchResults,
                          MinimalSource,
                          StudentSearchResultsAndAnswer,
                          MinimalAnswer)
import json
import fire
import uuid
import os
from tqdm import tqdm



class Core:
    def __init__(
        self,
        process_path=Path("data/processed"),
        output_path=Path("data/output"),
        chunks_file="chunks.json",
        bm25s_folder="bm25_index",
        search_results=Path("data/output/search_results/dataset_docs_public.json"),
    ):
        self.dataset = Path("data/raw")
        self.search_results = search_results
        self.process_path = process_path
        self.chunks_path = process_path / chunks_file
        self.bm25s_path = process_path / bm25s_folder
        self.search_results_path = output_path / "search_results"
        self.search_results_and_answer_path = output_path / "search_results_and_answer"


    def index(self, max_chunk_size=2000, dataset_type="docs", dataset=None):
        if dataset_type != "docs" and dataset_type != "code":
            raise (ValueError("The dataset is not valid"))
        if dataset is None:
            dataset_path = self.dataset
        else:
            dataset_path = Path(dataset)
        print(f"Ingesting {dataset_path} in {dataset_type} mode")

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

    def answer(self, query, k=1, save_directory=None):
        selected_chunks = Retrieving(self.bm25s_path,
                                     self.chunks_path,
                                     query, k).get_selected_chunks()
        model = Model("openai/Qwen/Qwen3-0.6B")
        reponse = Answering(model, selected_chunks, query).get_answer()
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        answer = {
                "question_id": str(uuid.uuid4()),
                "question": query,
                "retrieved_sources": sources,
                "answer": reponse
            }
        self._save_all_results_and_answers(save_directory, "answer.json", [MinimalAnswer(**answer)], k)


    def search_dataset(self, questions_path, k=1, save_directory=None):
        questions = get_questions(Path(questions_path))
        file_name = Path(questions_path).name
        self._init_results(save_directory, file_name, k)
        for question in questions:
            print(question.get("question"))
            selected_chunks = Retrieving(self.bm25s_path, self.chunks_path, question.get("question"), k).get_selected_chunks()
            sources = []
            for chunk in selected_chunks:
                sources.append(MinimalSource(**chunk))
            answer = MinimalSearchResults(
                question_id=question.get("question_id"),
                question=question.get("question"),
                retrieved_sources=sources
            )
            self._save_result(save_directory, file_name, answer)
        self.save_for_moulinette(save_directory, file_name, k)

    def search(self, query, k=1, save_directory=None):
        file_name = "search.json"
        self._init_results(save_directory, file_name, k)
        selected_chunks = Retrieving(self.bm25s_path,
                                     self.chunks_path,
                                     query, k).get_selected_chunks()
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        answer = MinimalSearchResults(
            question_id=str(uuid.uuid4()),
            question=query,
            retrieved_sources=sources
        )
        self._save_result(save_directory, file_name, answer)

    def answer_dataset(self, questions_path, k=1, save_directory=None):
        questions = get_questions(Path(questions_path))
        file_name = Path(questions_path).name
        self._init_results_and_answers(save_directory, file_name, k)
        model = Model("openai/Qwen/Qwen3-0.6B")
        for question in tqdm(questions, bar_format='[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}', colour='blue'):
            selected_chunks = Retrieving(
                self.bm25s_path,
                self.chunks_path,
                question.get("question"), k
            ).get_selected_chunks()
            reponse = Answering(model, selected_chunks, question.get("question")).get_answer()
            sources = []
            for chunk in selected_chunks:
                sources.append(MinimalSource(**chunk))
            answer = MinimalAnswer(
                question_id=question.get("question_id"),
                question=question.get("question"),
                retrieved_sources=sources,
                answer=reponse
            )
            self._save_results_and_answers(save_directory, file_name, answer)

    def evaluate(self, path_result, path_answered_questions):
        Evaluating(path_result, path_answered_questions)

    def _init_results(self, save_directory, file_name, k):
        if save_directory is None:
            save_path = self.search_results_path / file_name
        else:
            save_path = Path(save_directory) / file_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as file:
            file.write(StudentSearchResults(
                search_results=[],
                k=k
            ).model_dump_json(indent=2))

    def _init_results_and_answers(self, save_directory, file_name, k):
        if save_directory is None:
            save_path = self.search_results_and_answer_path / file_name
        else:
            save_path = Path(save_directory) / file_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as file:
            file.write(StudentSearchResultsAndAnswer(
                search_results=[],
                k=k
            ).model_dump_json(indent=2))


    def _save_result(self, save_directory, file_name, result):
        if save_directory is None:
            save_path = self.search_results_path / file_name
        else:
            save_path = Path(save_directory) / file_name

        with open(save_path, "r") as file:
            raw_data = file.read()
            data = StudentSearchResults.model_validate_json(raw_data)
        data.search_results.append(result)
        with open(save_path, "w") as file:
            file.write(data.model_dump_json(indent=2))



    def _save_results_and_answers(self, save_directory, file_name, result):
        if save_directory is None:
            save_path = self.search_results_and_answer_path / file_name
        else:
            save_path = Path(save_directory) / file_name
        with open(save_path, "r") as file:
            raw_data = file.read()
            data = StudentSearchResultsAndAnswer.model_validate_json(raw_data)
        data.search_results.append(result)
        with open(save_path, "w") as file:
            file.write(data.model_dump_json(indent=2))


    def save_for_moulinette(self, save_directory, file_name, k):
        try:
            if save_directory is None:
                save_path = self.search_results_path / file_name
            else:
                save_path = Path(save_directory) / file_name
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "r") as file:
                raw_data = file.read()
                results = StudentSearchResults.model_validate_json(raw_data)
            all = []
            for result in results.search_results:
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
            with (open("moulinette_format_result.json", "w")as file):
                file.write(json.dumps(data, indent=2))
        except Exception:
            raise (ValueError("Cannot write"))


def main():
    fire.Fire(Core)


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
