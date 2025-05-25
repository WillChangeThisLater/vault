import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class Chunk(BaseModel):
    index: int
    embedding: list[float]
    type: str

class Resource(BaseModel):
    uri: str
    hash: str
    model_id: str
    chunks: list[Chunk]

class SearchResult(BaseModel):
    uri: str
    index: int
    similarity: float
    type: str
