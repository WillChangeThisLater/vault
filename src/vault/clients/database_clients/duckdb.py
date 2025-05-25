import duckdb
import logging

from vault.models import Resource, Chunk, SearchResult
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.utils import get_default_db_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseClient(BaseDatabaseClient):

    def __init__(self, db_path: str = get_default_db_path()):
        self.connection = duckdb.connect(db_path)

    def _get_table_name(self, model_id: str) -> str:
        """Generates a table name based on the model_id and embedding size."""
        # strip trailing ':' in bedrock model ids
        if ":" in model_id:
            model_id = model_id.split(":")[0]
        return f"embeddings_{model_id.lower().replace('-', '_').replace('.', '_')}"

    def _table_exists(self, model_id: str) -> bool:
        """Checks if the specified table exists in the database."""
        table_name = self._get_table_name(model_id)
        query = f"""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_name = '{table_name}'
        LIMIT 1;
        """
        logger.debug(f"Executing SQL to check if table exists: {query}")
        result = self.connection.execute(query).fetchone()
        # Result is a tuple, and we are interested in the first element which is the count
        return result[0] > 0

    def _setup_table(self, table_name: str, embedding_size: int):
        """Creates a new table for embeddings with a specific fixed array size."""
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                resource_uri VARCHAR,
                resource_hash VARCHAR,
                resource_model_id VARCHAR,
                chunk_index INTEGER,
                chunk_embedding DOUBLE[{embedding_size}],
                chunk_type VARCHAR,
            );
        """
        logger.debug(f"setup_table: {query}")
        self.connection.execute(query)

    def list_resources(self, model_id: str) -> list[str]:
        """Lists all unique resource URIs for the specified model_id."""
        table_name = self._get_table_name(model_id)
        if not self._table_exists(model_id):
            raise ValueError(f"Table for model_id {model_id} not found")

        query = f"SELECT DISTINCT resource_uri FROM {table_name}"
        logger.debug(f"Executing SQL to list resources for model_id {model_id}: {query}")
        result = self.connection.execute(query).fetchall()

        # Extract the URIs from the result
        uris = [row[0] for row in result]
        return uris

    def delete(self, model_id: str, uri: str):
        table_name = self._get_table_name(model_id)
        if not self._table_exists(model_id):
            raise ValueError(f"Table for model_id {model_id} not found")

        delete_query = f"DELETE FROM {table_name} WHERE resource_uri = ?"
        self.connection.execute(delete_query, (uri, ))

    def insert(self, resource: Resource):
        """Inserts a new embedding or updates an existing one if the contents have changed."""
        if not resource.chunks:
            raise ValueError(f"Resource {resource} has no chunks")

        sample_chunk: Chunk = resource.chunks[0]
        embedding_size = len(sample_chunk.embedding)
        table_name = self._get_table_name(resource.model_id)

        # set up table if it does not exist
        if not self._table_exists(resource.model_id):
            logger.warning(f"No table for model {resource.model_id} found - creating...")
            self._setup_table(table_name, embedding_size)

        # delete existing references to the resource
        self.delete(resource.model_id, resource.uri)

        # Insert the file
        n_chunks = len(resource.chunks)
        for i, chunk in enumerate(resource.chunks):
            insert_query = f"""
                INSERT INTO {table_name} (resource_uri, resource_hash, resource_model_id, chunk_index, chunk_embedding, chunk_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            logger.debug(f"insert: inserting chunk {i + 1} of {n_chunks}: {insert_query}")
            self.connection.execute(insert_query, (
                resource.uri,
                resource.hash,
                resource.model_id,
                chunk.index,
                chunk.embedding,
                chunk.type,
            ))
        logger.debug(f"Resource '{resource.uri}' added to the vault.")

    def search(self, model_id: str, embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        embedding_size = len(embedding)
        table_name = self._get_table_name(model_id)
        if not self._table_exists(model_id):
            raise ValueError(f"No table for model {model_id} found")
    
        # Ensure the query array is of fixed size by explicitly casting to the correct type
        query_array = f"array_value({', '.join(map(str, embedding))})::DOUBLE[{embedding_size}]"
    
        # Select top chunks with a similarity score
        query = f"""
        WITH ranked_results AS (
            SELECT
                resource_uri,
                chunk_index,
                array_inner_product(chunk_embedding, {query_array}) AS similarity,
                RANK() OVER (PARTITION BY resource_uri ORDER BY array_inner_product(chunk_embedding, {query_array}) DESC) as rank,
                chunk_type
            FROM {table_name}
        )
        SELECT * FROM ranked_results
        WHERE rank = 1
        ORDER BY similarity DESC
        LIMIT ?
        """
    
        logger.debug(f"search: {query}")
        results = self.connection.execute(query, (top_k,)).fetchall()
        search_results = []
        for result in results:
            uri, index, similarity, _, chunk_type = result
            search_results.append(SearchResult(uri=uri, index=index, similarity=similarity, type=chunk_type))
        return search_results

    def debug_dump_table(self, model_id: str):
        """Dumps the content of the embeddings table to stdout."""
        table_name = self._get_table_name(model_id)
        query = f"SHOW TABLE {table_name}"
        logger.debug(f"Executing SQL to show table: {query}")
        result = self.connection.execute(query).fetchall()
        logger.debug(result)

        query = f"SELECT * FROM {table_name}"
        logger.debug(f"Executing SQL to select all from table: {query}")
        result = self.connection.execute(query).fetchall()
        for row in result:
            print(row)
