import boto3
import json
import itertools as it
import logging

from vault.clients.embedding_clients.base import BaseEmbeddingClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingClient(BaseEmbeddingClient):
    def __init__(self, model_id="amazon.titan-embed-text-v2:0"):
        self._model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name="us-east-1")
        self.max_tokens = 8192

    @property
    def model_id(self) -> str:
        return self._model_id

    def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding for given text."""
        request = json.dumps({"inputText": text})
        response = self.client.invoke_model(modelId=self.model_id, body=request)
        model_response = json.loads(response["body"].read())
        return model_response["embedding"]

    def chunk_text(self, text: str) -> list[str]:
        batches = it.batched(text, self.max_tokens)
        chunks = []
        for batch in batches:
            chunk = "".join(batch)
            chunks.append(chunk)
        return chunks
