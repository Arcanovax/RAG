from pydantic import BaseModel
from typing import Literal, Optional


class Index_model(BaseModel):
    max_chunk_size: int
    dataset_type: Literal["docs", "code", "all"]
    knowledge: Optional[str]


class Dataset_model(BaseModel):
    questions_path: str
    k: int
    save_directory: Optional[str]
    hybrid: Optional[bool]
    expand: Optional[bool]


class Query_model(BaseModel):
    query: str
    k: int
    save_directory: Optional[str]
    hybrid: Optional[bool]
    expand: Optional[bool]


class Answer_dataset_model(BaseModel):
    student_search_results_path: str
    save_directory: str
