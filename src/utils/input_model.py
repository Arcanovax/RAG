from pydantic import BaseModel, field_validator
import uuid
from typing import List, Literal, Optional


class Index_model(BaseModel):
    max_chunk_size: int
    dataset_type: Literal["docs", "code"]
    dataset: Optional[str]

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
