"""Pydantic schemas for datasets and results."""

from pydantic import BaseModel, Field
import uuid
from typing import List


class MinimalSource(BaseModel):
    """Location metadata for a chunk."""
    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """Question item without an answer."""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Question item with sources and answer."""
    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Dataset of RAG questions."""
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Minimal retrieval output for a question."""
    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Retrieval output with an answer."""
    answer: str


class StudentSearchResults(BaseModel):
    """Container for retrieval results."""
    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """Container for retrieval results and answers."""

    k: int
    search_results: list[MinimalAnswer]
