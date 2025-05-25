from abc import ABC

from vault.models import Resource, SearchResult

class BaseDatabaseClient(ABC):

    def list_resources(self, model_id: str) -> list[str]:
        pass

    def delete(self, model_id: str, uri: str):
        pass

    def insert(self, resource: Resource):
        pass

    def search(self, model_id: str, embedding: list[float], top_k: int) -> list[SearchResult]:
        pass
