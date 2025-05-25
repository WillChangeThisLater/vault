from vault.clients.embedding_clients.base import BaseEmbeddingClient
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.clients.llm_clients.base import BaseLLMClient

class BasePlugin:

    def can_handle(self, uri: str) -> bool:
        """Return True if this plugin can handle the given URI, else False."""
        raise NotImplementedError

    def handle(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        """Process the URI according to the plugin's purpose."""
        raise NotImplementedError
