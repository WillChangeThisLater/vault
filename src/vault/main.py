import click
import logging
import importlib
import sys

from vault.services import ModelService
from vault.utils import filter_uris_by_regex
from vault.models import SearchResult

from vault.config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger('vault')

def set_log_level(log_level):
    """Set the logging level."""
    try:
        numerical_level = getattr(logging, log_level.upper())
        logging.getLogger().setLevel(numerical_level)
    except AttributeError:
        raise ValueError(f"Invalid log level: {log_level}")


def setup_clients() -> dict:
    # get the config file
    # TODO: set up config file for user (w/ reasonable defaults) if one does not exist
    config = load_config()

    # Obtain configurations
    default_config = config["default"]
    embedding_provider = default_config["embedding_provider"]
    llm_provider = default_config["llm_provider"]
    database_provider = default_config["database_provider"]

    # get classes for embedding and llm clients
    module = importlib.import_module(f"vault.clients.embedding_clients.{embedding_provider}")
    EmbeddingClient = getattr(module, "EmbeddingClient")
    module = importlib.import_module(f"vault.clients.llm_clients.{llm_provider}")
    LLMClient = getattr(module, "LLMClient")
    module = importlib.import_module(f"vault.clients.database_clients.{database_provider}")
    DatabaseClient = getattr(module, "DatabaseClient")

    # set up clients
    embedding_model_id = config["embedding_clients"][embedding_provider]["model_id"]
    llm_model_id = config["llm_clients"][llm_provider]["model_id"]
    db_path = config["database_clients"][database_provider]["db_path"]
    embedding_client = EmbeddingClient(embedding_model_id)
    llm_client = LLMClient(llm_model_id)
    database_client = DatabaseClient(db_path)

    return {
        "embedding_client": embedding_client,
        "database_client": database_client,
        "llm_client": llm_client
    }

@click.group()
def vault():
    """A CLI tool for embedding and vector search."""
    pass

@click.command()
@click.argument('uris', nargs=-1)
@click.option('--log-level', default='WARNING', help='Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).')
@click.option('--quick', is_flag=True, help='Enable quick processing mode. Embed only the first and last text chunks.')
def add(uris, log_level, quick):
    """Add one or more files to the vault."""
    set_log_level(log_level)

    # Create clients
    clients = setup_clients()
    model_service = ModelService(**clients)

    # Process each URI
    for uri in uris:
        try:
            model_service.add(uri, quick=quick)
            logger.info(f"Successfully added {uri} to the vault.")
        except ValueError as e:
            logger.error(f"Failed to add {uri}: {e}")

@click.command()
@click.argument('pattern')
@click.option('--log-level', default='INFO', help='Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).')
def rm(pattern, log_level):
    """Remove resource(s) from the vault."""
    set_log_level(log_level)

    clients = setup_clients()
    model_service = ModelService(**clients)

    # TODO: this is a little ugly
    embedding_client = clients["embedding_client"]
    database_client = clients["database_client"]
    all_uris = database_client.list_resources(embedding_client.model_id)
    matched_uris = filter_uris_by_regex(all_uris, pattern)

    if len(matched_uris) == 0:
        logger.warning(f"No resources found matching pattern: {pattern}")
        return

    if len(matched_uris) == 1:
        model_service.delete(matched_uris[0])
        return

    print(f"You are about to delete {len(matched_uris)} resources. Are you sure? (Y/N)")
    confirmation = input().strip().lower()[0]

    if confirmation == 'y':
        for uri in matched_uris:
            model_service.delete(uri)
            logger.info(f"Deleted: {uri}")
    else:
        print("Deletion cancelled")

@click.command()
@click.argument('query')
@click.option('--top-k', default=1, help='Number of top similar results to return.')
@click.option('--show-scores', is_flag=True, help='Show similarity scores alongside the result URIs.')
@click.option('--min-score', default=None, type=float, help='Minimum similarity score required for results.')
@click.option('--log-level', default='WARNING', help='Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).')
def search(query, top_k, show_scores, min_score, log_level):
    """Perform a vector search with a given query."""
    set_log_level(log_level)

    clients = setup_clients()
    model_service = ModelService(**clients)

    results: list[SearchResult] = model_service.search(query, top_k)

    filtered_results = results
    if min_score is not None:
        filtered_results = [result for result in results if result.similarity >= min_score]

    if not filtered_results:
        logger.warning(f"No results found with a similarity score above {min_score}.")
        return


    max_uri_length = max(len(result.uri) for result in filtered_results)
    for result in filtered_results:
        if show_scores:
            # Format the output with fixed width for URI and score columns
            click.echo(f"{result.uri:{max_uri_length}}    {result.similarity:.4f}")
        else:
            click.echo(result.uri)

@click.command()
@click.option('--log-level', default='WARNING', help='Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).')
def ls(log_level):
    """Dump all URIs ingested by the database."""
    set_log_level(log_level)

    clients = setup_clients()
    model_service = ModelService(**clients)
    uris = model_service.list_resources()
    uris.sort()

    for uri in uris:
        click.echo(uri)

# Add commands to the vault group
def main():
    vault.add_command(add)
    vault.add_command(rm)
    vault.add_command(search)
    vault.add_command(ls)

    vault()
