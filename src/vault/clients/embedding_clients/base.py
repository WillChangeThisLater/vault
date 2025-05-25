from abc import ABC, abstractmethod

class BaseEmbeddingClient(ABC):

    def generate_embedding(self, text: str) -> list[float]:
        """Abstract method for generating an embedding for text."""
        pass

    def chunk_text(self, text: str) -> list[str]:
        """Abstract method for chunking text"""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        pass
