from .chunking import Chunking
from .retrieving import Retrieving
from .indexing import Indexing
from .evaluating import Evaluating
from .answering import Answering, Model
from pathlib import Path
from .utils.model import (StudentSearchResults,
                          MinimalSearchResults,
                          MinimalSource,
                          StudentSearchResultsAndAnswer,
                          MinimalAnswer)
from .utils.input_model import (Index_model,
                                Search_dataset_model,
                                Query_model,
                                BaseModel,
                                Answer_dataset_model)
import json
import fire
import uuid
from tqdm import tqdm


class Core:
    """CLI entrypoint for indexing, retrieval, and answering."""

    def __init__(
        self,
    ):
        """Initialize CLI defaults and paths."""
        self._model_name = "openai/Qwen/Qwen3-0.6B"
        self._knowledge = Path("data/raw")
        self._search_results = Path(
            "data/output/search_results/dataset_docs_public.json"
        )
        self._process_path = Path("data/processed")
        self._output_path = Path("data/output")
        self._chunks_path = self._process_path / "chunks.json"
        self._bm25s_path = self._process_path / "bm25_index"
        self._search_results_path = self._output_path / "search_results"
        self._search_results_and_answer_path = self._output_path / "search_results_and_answer"


    def index(self, max_chunk_size=2000, dataset_type="all", knowledge=None):
        """Index a dataset into chunk and retrieval indices.

        Args:
            max_chunk_size (int): Maximum size of a chunk.
            dataset_type (str): Dataset type ("docs", "code", or "all").
            knowledge (str | None): Optional dataset path override.
        """
        args = self._validate_args(
            Index_model,
            max_chunk_size=max_chunk_size,
            dataset_type=dataset_type,
            knowledge=knowledge,
        )
        if args is None:
            return
        if args.knowledge is None:
            dataset_path = self._knowledge
        else:
            dataset_path = Path(args.knowledge)
        print(f"Ingesting {dataset_path} in {args.dataset_type} mode")

        self.all_chunks = Chunking(
            dataset_path,
            args.max_chunk_size,
            self._chunks_path,
            args.dataset_type
        ).get_all_chunks()

        if len(self.all_chunks) == 0:
            raise (ValueError("No files found"))
        Indexing(
            self._bm25s_path,
            self.all_chunks,
            args.dataset_type,
            self._process_path,
        )

    def answer(
        self,
        query: str,
        k=10,
        save_directory=None,
        hybrid=False,
        expand=False,
    ):
        """Answer a single query using retrieved chunks.

        Args:
            query (str): Question about the dataset.
            k (int): Number of chunks to retrieve.
            save_directory (str | None): Optional output directory.
            hybrid (bool): Enable hybrid retrieval.
            expand (bool): Enable query expansion.
        """
        args = self._validate_args(
            Query_model, query=query,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return
        retriver = Retrieving(self._bm25s_path, self._chunks_path,
                              k, args.hybrid, args.expand)
        save_path = self._init_results_and_answers(args.save_directory,
                                                   "answer.json", args.k)
        selected_chunks = retriver.retrieve(args.query)
        print(f"Retrieve {len(selected_chunks)} chunk(s)")
        answerer = Answering(self._model_name)
        reponse = answerer.answer_query(selected_chunks, query)
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        answer = {
                "question_id": str(uuid.uuid4()),
                "question": args.query,
                "retrieved_sources": sources,
                "answer": reponse
            }
        self._save_results_and_answers(save_path, MinimalAnswer(**answer))
        print("Saved answer to", save_path)

    def search_dataset(self, dataset_path, k=10, save_directory=None,
                       hybrid=False, expand=False):
        """Retrieve chunks for every question in a dataset file.

        Args:
            dataset_path (str): Path to dataset questions JSON.
            k (int): Number of chunks to retrieve.
            save_directory (str | None): Optional output directory.
            hybrid (bool): Enable hybrid retrieval.
            expand (bool): Enable query expansion.
        """
        args = self._validate_args(
            Search_dataset_model,
            questions_path=dataset_path,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return

        questions = self._get_questions(Path(args.questions_path))
        file_name = Path(args.questions_path).name
        save_path = self._init_results(args.save_directory, file_name, args.k)
        retriver = Retrieving(self._bm25s_path, self._chunks_path,
                              args.k, args.hybrid, args.expand)

        for question in tqdm(
            questions,
            bar_format=(
                "[{elapsed}<{remaining}]{n_fmt}/{total_fmt} | "
                "{l_bar}{bar} {rate_fmt}{postfix}"
            ),
            colour="blue",
        ):
            selected_chunks = retriver.retrieve(question.get("question"))
            sources = []
            for chunk in selected_chunks:
                sources.append(MinimalSource(**chunk))
            answer = MinimalSearchResults(
                question_id=question.get("question_id"),
                question=question.get("question"),
                retrieved_sources=sources
            )
            self._save_result(save_path, answer)

        print("Saved student_search_results to", save_path)
        self._save_for_moulinette(save_path, k)

    def search(self, query: str, k=10, save_directory=None,
               hybrid=False, expand=False):
        """Retrieve chunks for a single query.

        Args:
            query (str): Question about the dataset.
            k (int): Number of chunks to retrieve.
            save_directory (str | None): Optional output directory.
            hybrid (bool): Enable hybrid retrieval.
            expand (bool): Enable query expansion.
        """
        args = self._validate_args(
            Query_model, query=query,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return
        file_name = "search.json"
        save_path = self._init_results(args.save_directory, file_name, k)
        retriver = Retrieving(self._bm25s_path, self._chunks_path, k,
                              args.hybrid, args.expand)

        selected_chunks = retriver.retrieve(args.query)
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        answer = MinimalSearchResults(
            question_id=str(uuid.uuid4()),
            question=args.query,
            retrieved_sources=sources
        )
        self._save_result(save_path, answer)
        print("Saved search to", save_path)

    def answer_dataset(self, student_search_results_path, save_directory=None):
        """Generate answers from an existing retrieval results file.

        Args:
            student_search_results_path (str): Path to search results JSON.
            save_directory (str | None): Optional output directory.
        """
        args = self._validate_args(
            Answer_dataset_model,
            student_search_results_path=student_search_results_path,
            save_directory=save_directory
        )
        if args is None:
            return
        search_results, k = self._get_search_results(
            args.student_search_results_path
        )
        print(
            f"Loaded {len(search_results)} questions from "
            f"{student_search_results_path}"
        )

        file_name = Path(args.student_search_results_path).name
        save_path = self._init_results_and_answers(
            args.save_directory, file_name, k
        )

        answerer = Answering(self._model_name)

        nb_processed = 0
        for result in tqdm(
            search_results,
            bar_format=(
                "[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | "
                "{l_bar}{bar} {rate_fmt}{postfix}"
            ),
            colour="blue",
        ):
            reponse = answerer.answer_dataset(result, self._chunks_path)
            answer = MinimalAnswer(
                question_id=result.question_id,
                question=result.question,
                retrieved_sources=result.retrieved_sources,
                answer=reponse
            )
            self._save_results_and_answers(save_path, answer)
            nb_processed += 1
        print(f"Processed {nb_processed} of {len(search_results)} questions")
        print("Saved student_search_results_and_answer to", save_path)

    def evaluate(self, path_result: str, path_answered_questions: str):
        """Evaluate retrieval results against labeled answers.

        Args:
            path_result (str): Path to search results JSON.
            path_answered_questions (str): Path to answered questions JSON.
        """
        Evaluating(path_result, path_answered_questions)

    def _init_results(self, save_directory: str, file_name: str, k):
        """Create a results file initialized with empty entries.

        Args:
            save_directory (str | None): Output directory.
            file_name (str): Output file name.
            k (int): Recall cut-off used for retrieval.

        Returns:
            Path: Path to the initialized results file.
        """
        if save_directory is None:
            save_path = self._search_results_path / file_name
        else:
            save_path = Path(save_directory) / file_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as file:
            file.write(StudentSearchResults(
                search_results=[],
                k=k
            ).model_dump_json(indent=2))
        return save_path

    def _init_results_and_answers(self, save_directory, file_name, k):
        """Create a results-and-answers file with empty entries.

        Args:
            save_directory (str | None): Output directory.
            file_name (str): Output file name.
            k (int): Recall cut-off used for retrieval.

        Returns:
            Path: Path to the initialized results-and-answers file.
        """
        if save_directory is None:
            save_path = self._search_results_and_answer_path / file_name
        else:
            save_path = Path(save_directory) / file_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as file:
            file.write(StudentSearchResultsAndAnswer(
                search_results=[],
                k=k
            ).model_dump_json(indent=2))
        return save_path

    def _save_result(self, save_path: str,
                     result: MinimalSearchResults):
        """Append a search result to a results file.

        Args:
            save_path (str): Path to the results file.
            result (MinimalSearchResults): Result to append.
        """
        with open(save_path, "r") as file:
            raw_data = file.read()
            data = StudentSearchResults.model_validate_json(raw_data)
        data.search_results.append(result)
        with open(save_path, "w") as file:
            file.write(data.model_dump_json(indent=2))

    def _save_results_and_answers(self, save_path: str,
                                  result: MinimalAnswer):
        """Append a result with answer to the output file.

        Args:
            save_path (str): Path to the results-and-answers file.
            result (MinimalAnswer): Result and answer to append.
        """
        with open(save_path, "r") as file:
            raw_data = file.read()
            data = StudentSearchResultsAndAnswer.model_validate_json(raw_data)
        data.search_results.append(result)
        with open(save_path, "w") as file:
            file.write(data.model_dump_json(indent=2))

    def _save_for_moulinette(self, save_path: str,
                             k: int):
        """Write a moulinette-compatible output file.

        Args:
            save_path (str): Path to the source results file.
            k (int): Recall cut-off used for retrieval.
        """
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "r") as file:
                raw_data = file.read()
                results = StudentSearchResults.model_validate_json(raw_data)
            all = []
            for result in results.search_results:
                sources = []
                for chunk in result.retrieved_sources:
                    sources.append(
                        {
                            "file_path": chunk.file_path,
                            "first_character_index": (
                                chunk.first_character_index
                            ),
                            "last_character_index": (
                                chunk.last_character_index
                            ),
                        }
                    )
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

    def _validate_args(self, model: BaseModel, **kwargs):
        """Validate CLI arguments with a Pydantic model.

        Args:
            model (BaseModel): Pydantic model class.
            **kwargs: Values to validate.

        Returns:
            BaseModel | None: Validated model or None on error.
        """
        try:
            return model(**kwargs)
        except Exception as e:
            for error in e.errors():
                print(f"Error: {error.get('loc')[0]} ({error.get('msg')})")
            return None

    def _get_questions(self, file: Path):
        """Load questions from a dataset file.

        Args:
            file (Path): Path to the dataset file.

        Returns:
            list: List of questions.
        """
        try:
            with (open(file, "r") as file):
                data = file.read()
                data = json.loads(data)
                return data.get("rag_questions")
        except Exception:
            raise ValueError("No questions found")

    def _get_search_results(self, file_path: Path):
        """Load search results from a JSON file.

        Args:
            file_path (Path): Path to the results file.

        Returns:
            tuple[list, int]: Search results and configured k.
        """
        try:
            with open(file_path, "r") as file:
                raw_data = file.read()
                results = StudentSearchResults.model_validate_json(raw_data)
                return (results.search_results), (results.k)
        except Exception:
            raise ValueError("The search results doesn t exist")


def main():
    """Run the CLI entrypoint."""
    try:
        fire.Fire(Core)
    except Exception as e:
        print("[ERROR]:", e)


if __name__ == "__main__":
    main()
