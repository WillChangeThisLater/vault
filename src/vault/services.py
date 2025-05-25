import logging

from vault.clients.embedding_clients.base import BaseEmbeddingClient
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.clients.llm_clients.base import BaseLLMClient
from vault.plugins import load_plugins

logger = logging.getLogger(__name__)

class ModelService:

    def __init__(
        self,
        embedding_client: BaseEmbeddingClient,
        database_client: BaseDatabaseClient,
        llm_client: BaseLLMClient
    ):
        self.embedding_client = embedding_client
        self.database_client = database_client
        self.llm_client = llm_client

    def delete(self, uri: str):
        self.database_client.delete(self.embedding_client.model_id, uri)

    def search(self, query: str, top_k: int = 5):
        embedding = self.embedding_client.generate_embedding(query)
        model_id = self.embedding_client.model_id
        results = self.database_client.search(model_id, embedding, top_k)
        return results

    def add(self, uri: str, quick: bool = False) -> None:
        plugins = load_plugins()
        for plugin in plugins:
            if plugin.can_handle(uri):
                plugin.handle(uri, self.embedding_client, self.database_client, self.llm_client, quick)
                return
    
        raise ValueError(f"No suitable handler found for URI '{uri}'")

    def list_resources(self):
        return self.database_client.list_resources(self.embedding_client.model_id)
