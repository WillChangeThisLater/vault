from openai import OpenAI
from vault.clients.embedding_clients.base import BaseEmbeddingClient

class EmbeddingClient(BaseEmbeddingClient):
    def __init__(self, model_id="text-embedding-3-large"):
        self._model_id = model_id
        self.client = OpenAI()

    @property
    def model_id(self) -> str:
        return self._model_id

    def generate_embedding(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model_id,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    def chunk_text(self, text: str) -> list[str]:
        max_text_size = 4096  # Assume a reasonable chunk size for the model
        return [text[i:i + max_text_size] for i in range(0, len(text), max_text_size)]
