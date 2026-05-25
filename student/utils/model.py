from pydantic import BaseModel, Field
import uuid
from typing import List


class MinimalSource(BaseModel):
    """Minimal source span metadata.

    Attributes:
        file_path: Source file path.
        first_character_index: Span start index.
        last_character_index: Span end index.
    """
    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """Question without sources or answer.

    Attributes:
        question_id: Unique question id.
        question: Question text.
    """
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Question with sources and answer.

    Attributes:
        sources: List of gold sources.
        answer: Reference answer.
    """
    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Dataset container for RAG questions.

    Attributes:
        rag_questions: List of answered or unanswered questions.
    """
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Minimal retrieval output for one question.

    Attributes:
        question_id: Question id.
        question: Question text.
        retrieved_sources: Retrieved sources.
    """
    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Retrieval output with a generated answer.

    Attributes:
        answer: Generated answer text.
    """
    answer: str


class StudentSearchResults(BaseModel):
    """Top-k retrieval results for multiple questions.

    Attributes:
        search_results: List of retrieval results.
        k: Retrieval cut-off.
    """
    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """Retrieval outputs augmented with generated answers.

    Attributes:
        k: Number of top retrieved sources used per question.
        search_results: Results containing retrieved sources and answers.
    """

    k: int
    search_results: list[MinimalAnswer]
