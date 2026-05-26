"""Pydantic schemas for CLI arguments."""

from pydantic import BaseModel
from typing import Literal, Optional


class Index_model(BaseModel):
    """Arguments for the index command."""
    max_chunk_size: int
    dataset_type: Literal["docs", "code", "all"]
    knowledge: Optional[str] = None


class Dataset_model(BaseModel):
    """Arguments for dataset search command."""
    questions_path: str
    k: int
    save_directory: Optional[str] = None
    hybrid: Optional[bool] = None
    expand: Optional[bool] = None


class Query_model(BaseModel):
    """Arguments for single query commands."""
    query: str
    k: int
    save_directory: Optional[str] = None
    hybrid: Optional[bool] = None
    expand: Optional[bool] = None


class Answer_dataset_model(BaseModel):
    """Arguments for dataset answer command."""
    student_search_results_path: str
    save_directory: Optional[str] = None
