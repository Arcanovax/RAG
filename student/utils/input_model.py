from pydantic import BaseModel
from typing import Literal, Optional


class Index_model(BaseModel):
    """CLI arguments for the index command.

    Attributes:
        max_chunk_size: Maximum chunk size.
        dataset_type: Dataset type ("docs", "code", or "all").
        knowledge: Optional dataset path.
    """
    max_chunk_size: int
    dataset_type: Literal["docs", "code", "all"]
    knowledge: Optional[str]


class Dataset_model(BaseModel):
    """CLI arguments for dataset search.

    Attributes:
        questions_path: Path to the questions file.
        k: Number of chunks to retrieve.
        save_directory: Optional output directory.
        hybrid: Enable hybrid retrieval.
        expand: Enable query expansion.
    """
    questions_path: str
    k: int
    save_directory: Optional[str]
    hybrid: Optional[bool]
    expand: Optional[bool]


class Query_model(BaseModel):
    """CLI arguments for single-query search or answer.

    Attributes:
        query: Input question.
        k: Number of chunks to retrieve.
        save_directory: Optional output directory.
        hybrid: Enable hybrid retrieval.
        expand: Enable query expansion.
    """
    query: str
    k: int
    save_directory: Optional[str]
    hybrid: Optional[bool]
    expand: Optional[bool]


class Answer_dataset_model(BaseModel):
    """CLI arguments for dataset answering.

    Attributes:
        student_search_results_path: Path to search results JSON.
        save_directory: Output directory for answers.
    """
    student_search_results_path: str
    save_directory: Optional[str]
