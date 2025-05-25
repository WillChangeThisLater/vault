from abc import ABC, abstractmethod
from PIL import Image

class BaseLLMClient(ABC):

    def summarize(self, prompt: str) -> str:
        pass

    def summarize_image(self, image: Image, prompt: str = "") -> str:
        """Abstract method for generating an embedding for text."""
        pass
