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
                                Dataset_model,
                                Query_model,
                                BaseModel)
import json
import fire
import uuid
from tqdm import tqdm


class Core:
    def __init__(
        self,
    ):
        """Init the Core function that handle all the CLI
        """
        self._model_name = "openai/Qwen/Qwen3-0.6B"
        self._dataset = Path("data/raw")
        self._search_results = Path("data/output/search_results/dataset_docs_public.json")
        self._process_path = Path("data/processed")
        self._output_path = Path("data/output")
        self._chunks_path = self._process_path / "chunks.json"
        self._bm25s_path = self._process_path / "bm25_index"
        self._search_results_path = self._output_path / "search_results"
        self._search_results_and_answer_path = self._output_path / "search_results_and_answer"


    def index(self, max_chunk_size=2000, dataset_type="all", dataset=None):
        """Index the dataset in chunks with langchain, if the dataset is in
        docs mode, a chroma database is created to handle semantic search

        Args:
            max_chunk_size (int, optional): Maximum size of a chunk.
            dataset_type (str, optional): Type of the dataset
            ("docs", "code" or "all"). Defaults to "all".
            dataset (str, optional): Custom dataset path. Defaults to None.
        """
        args = self._validate_args(Index_model, max_chunk_size=max_chunk_size,
                                   dataset_type=dataset_type, dataset=dataset)
        if args is None:
            return
        if args.dataset is None:
            dataset_path = self._dataset
        else:
            dataset_path = Path(args.dataset)
        print(f"Ingesting {dataset_path} in {args.dataset_type} mode")

        self.all_chunks = Chunking(
            dataset_path,
            args.max_chunk_size,
            self._chunks_path,
            args.dataset_type
        ).get_all_chunks()

        if len(self.all_chunks) == 0:
            raise (ValueError("No files found"))
        Indexing(self._bm25s_path, self.all_chunks,
                 args.dataset_type, self._process_path)


    def answer(self, query:str, k=10, save_directory=None, hybrid=False, expand=False):
        """Answer the query with the model according to the selected chunks
        retrieve from the retriever

        Args:
            query (str): question about the dataset
            k (int, optional): Number of selected chunks. Defaults to 10.
            save_directory (str, optional): Custom save directory.
            hybrid (bool, optional): Add hybrid retrive .
            expand (bool, optional): Expand the query for the retrieve.
        """
        args = self._validate_args(
            Query_model,query=query,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return
        retriver = Retrieving(
            self._bm25s_path,
            self._chunks_path,
            k, hybrid, expand)
        self._init_results_and_answers(args.save_directory, "answer.json",
                                       args.k)
        selected_chunks = retriver.retrieve(args.query)
        model = Model(self._model_name)
        reponse = Answering(model, selected_chunks, args.query).get_answer()
        sources = []
        for chunk in selected_chunks:
            sources.append(MinimalSource(**chunk))
        answer = {
                "question_id": str(uuid.uuid4()),
                "question": args.query,
                "retrieved_sources": sources,
                "answer": reponse
            }
        self._save_results_and_answers(args.save_directory, "answer.json",
                                       MinimalAnswer(**answer))

    def search_dataset(self, questions_path, k=10, save_directory=None,
                       hybrid=False, expand=False):
        """Find the most relevant chunks for each questions of the list

        Args:
            questions_path (str): list of questions about the dataset
            k (int, optional): Number of selected chunks. Defaults to 10.
            save_directory (str, optional): Custom save directory.
            hybrid (bool, optional): Add hybrid retrive. Defaults to False.
            expand (bool, optional): Expand the query for the retrieve.
        """
        args = self._validate_args(
            Dataset_model,
            questions_path=questions_path,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return

        questions = self._get_questions(Path(args.questions_path))
        file_name = Path(args.questions_path).name
        self._init_results(args.save_directory, file_name, args.k)
        retriver = Retrieving(self._bm25s_path, self._chunks_path,
                              args.k, args.hybrid, args.expand)

        for question in tqdm(questions, bar_format='[{elapsed}<{remaining}]{n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}', colour='blue'):
            selected_chunks = retriver.retrieve(question.get("question"))
            sources = []
            for chunk in selected_chunks:
                sources.append(MinimalSource(**chunk))
            answer = MinimalSearchResults(
                question_id=question.get("question_id"),
                question=question.get("question"),
                retrieved_sources=sources
            )
            self._save_result(args.save_directory, file_name, answer)
        self._save_for_moulinette(args.save_directory, file_name, k)

    def search(self, query: str, k=10, save_directory=None,
               hybrid=False, expand=False):
        """Find the most relevant chunks to answer the query

        Args:
            query (str): question about the dataset
            k (int, optional): Number of selected chunks. Defaults to 10.
            save_directory (str, optional): Custom save directory.
            hybrid (bool, optional): Add hybrid retrive. Defaults to False.
            expand (bool, optional): Expand the query for the retrieve.
        """
        args = self._validate_args(
            Query_model, query=query,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return
        file_name = "search.json"
        self._init_results(args.save_directory, file_name, k)
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
        self._save_result(args.save_directory, file_name, answer)

    def answer_dataset(self, questions_path, k=1, save_directory=None, hybrid=False, expand=False):
        """Answer all the questions with the model of the list according to
        the selected chunks retrieve from the retriever

        Args:
            questions_path (str): question about the dataset
            k (int, optional): Number of selected chunks. Defaults to 10.
            save_directory (str, optional): Custom save directory.
            hybrid (bool, optional): Add hybrid retrive.
            expand (bool, optional): Expand the query for the retrieve.
        """
        args = self._validate_args(
            Dataset_model,
            questions_path=questions_path,
            k=k, save_directory=save_directory, hybrid=hybrid, expand=expand
        )
        if args is None:
            return

        questions = self._get_questions(Path(args.questions_path))
        file_name = Path(args.questions_path).name
        self._init_results_and_answers(args.save_directory, file_name, args.k)
        model = Model(self._model_name)
        retriver = Retrieving(self._bm25s_path, self._chunks_path,
                              args.k, args.hybrid, args.expand)

        for question in tqdm(questions, bar_format='[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}', colour='blue'):
            selected_chunks = retriver.retrieve(question.get("question"))
            reponse = Answering(model, selected_chunks,
                                question.get("question")).get_answer()
            sources = []
            for chunk in selected_chunks:
                sources.append(MinimalSource(**chunk))
            answer = MinimalAnswer(
                question_id=question.get("question_id"),
                question=question.get("question"),
                retrieved_sources=sources,
                answer=reponse
            )
            self._save_results_and_answers(args.save_directory,
                                           file_name, answer)

    def evaluate(self, path_result: str, path_answered_questions: str):
        """Evaluate the pertinence of the results found

        Args:
            path_result (str): results found
            path_answered_questions (str): real answers
        """
        Evaluating(path_result, path_answered_questions)

    def _init_results(self, save_directory: str, file_name: str, k):
        """Initialize the file for results

        Args:
            save_directory (str): Save directory
            file_name (str): Save file name
            k (int): Number of recall
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

    def _init_results_and_answers(self, save_directory, file_name, k):
        """Initialize the file for results and answers

        Args:
            save_directory (str): Save directory
            file_name (str): Save file name
            k (int): Number of recall
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

    def _save_result(self, save_directory: str, file_name: str,
                     result: MinimalSearchResults):
        """Save the result in the file

        Args:
            save_directory (str): Save directory
            file_name (str): Save file name
            result (MinimalSearchResults): Result to save
        """
        if save_directory is None:
            save_path = self._search_results_path / file_name
        else:
            save_path = Path(save_directory) / file_name

        with open(save_path, "r") as file:
            raw_data = file.read()
            data = StudentSearchResults.model_validate_json(raw_data)
        data.search_results.append(result)
        with open(save_path, "w") as file:
            file.write(data.model_dump_json(indent=2))

    def _save_results_and_answers(self, save_directory: str, file_name: str,
                                  result: MinimalAnswer):
        """Save the result and answer in the file

        Args:
            save_directory (str): Save directory
            file_name (str): Save file name
            result (MinimalAnswer): Result and answer to save
        """
        if save_directory is None:
            save_path = self._search_results_and_answer_path / file_name
        else:
            save_path = Path(save_directory) / file_name
        with open(save_path, "r") as file:
            raw_data = file.read()
            data = StudentSearchResultsAndAnswer.model_validate_json(raw_data)
        data.search_results.append(result)
        with open(save_path, "w") as file:
            file.write(data.model_dump_json(indent=2))

    def _save_for_moulinette(self, save_directory: str, file_name: str,
                             k: int):
        """Get the save and creates a file compatible with the moulinette

        Args:
            save_directory (str): Save directory
            file_name (str): Save file name
            k (int): Number of recall
        """
        try:
            if save_directory is None:
                save_path = self._search_results_path / file_name
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

    def _validate_args(self, model: BaseModel, **kwargs):
        """Validate all the args with a pydantic model

        Args:
            model (BaseModel): model

        Returns:
            BaseModel: Arguments
        """
        try:
            return model(**kwargs)
        except Exception as e:
            for error in e.errors():
                print(f"Error: {error.get('loc')[0]} ({error.get('msg')})")
            return None

    def _get_questions(self, file: Path):
        """Get all the questions from the file

        Args:
            file (Path): file path

        Returns:
            list: All the questions
        """
        try:
            with (open(file, "r")as file):
                data = file.read()
                data = json.loads(data)
                return data.get("rag_questions")
        except Exception:
            raise (ValueError("No questions found"))


def main():
    try:
        fire.Fire(Core)
    except Exception as e:
        print("[ERROR]:", e)


if __name__ == "__main__":
    main()
