import logging
import os
from urllib.parse import urlparse
from vault.plugins.base_plugin import BasePlugin
from vault.models import Resource, Chunk
from vault.clients.embedding_clients.base import BaseEmbeddingClient
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.clients.llm_clients.base import BaseLLMClient
from atlassian import Confluence, Jira

logger = logging.getLogger(__name__)

class AtlassianPlugin(BasePlugin):

    def can_handle(self, uri: str) -> bool:
        try:
            result = urlparse(uri)
            # Detect both Confluence pages and JIRA tickets
            return all([result.scheme, result.netloc]) and ('/wiki/spaces/' in result.path or '/browse/' in result.path)
        except ValueError:
            return False

    def handle(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        # Extract Confluence credentials from the URI or environment variables
        atlassian_url = urlparse(uri).netloc
        username, password = os.environ["CONFLUENCE_API_USERNAME"], os.environ["CONFLUENCE_API_KEY"]

        if "/browse/" in urlparse(uri).path:
            client = Jira(
                url=f'https://{atlassian_url}',
                username=username,
                password=password,
                cloud=True
            )
            self.handle_jira_ticket(uri, client, embedding_client, database_client, llm_client, quick)
        else:
            # Initialize Confluence client
            client = Confluence(
                url=f'https://{atlassian_url}',
                username=username,
                password=password,
                cloud=True
            )
            # Identify if the URI is pointing to a specific page or a space
            if "pages" in urlparse(uri).path:
                self.handle_page(uri, client, embedding_client, database_client, llm_client, quick)
            else:
                self.handle_space(uri, client, embedding_client, database_client, llm_client, quick)

    def handle_jira_ticket(self, uri: str, jira: Jira, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        # Extract ticket ID from the URI
        ticket_id = uri.split('/')[-1]

        # Fetch JIRA ticket details
        ticket = jira.issue(ticket_id)

        ticket_description = ticket['fields'].get('description', '')
        ticket_summary = ticket['fields'].get('summary', '')
        ticket_status = ticket['fields'].get('status', {}).get('name', 'Unknown')
        reporter = ticket['fields'].get('reporter', {}).get('displayName', 'Unknown')

        comments = []
        for comment in jira.issue_get_comments(ticket_id)['comments']:
            comments.append(f"{comment['author']['displayName']} commented: {comment['body']}")

        # Format a detailed description
        detail_description = f"""
            JIRA Ticket: {uri}
            Summary: {ticket_summary}
            Description: {ticket_description}
            Status: {ticket_status}
            Reporter: {reporter}
            Comments: {' | '.join(comments)}
        """

        # Chunk, embed, and store this information
        text_chunks = embedding_client.chunk_text(detail_description)
        if quick and len(text_chunks) > 1:
            text_chunks = [text_chunks[0], text_chunks[-1]]

        chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                  for i, text in enumerate(text_chunks)]

        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)

    def handle_page(self, uri: str, confluence: Confluence, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        # Extract page ID from the URI
        page_id = uri.split('/')[-2]

        # Fetch page content
        # Add header and footer so we know where the page is from
        page_content = confluence.get_page_by_id(page_id, expand='body.storage')
        content = f"Contents from confluence page: {uri}"
        content += page_content['body']['storage']['value']
        content += f"Contents from confluence page: {uri}"

        # Chunk and embed the content
        text_chunks = embedding_client.chunk_text(content)
        if quick and len(text_chunks) > 1:
            text_chunks = [text_chunks[0], text_chunks[-1]]

        chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                  for i, text in enumerate(text_chunks)]

        # Create Resource and insert into database
        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)

    def handle_space(self, uri: str, confluence: Confluence, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):

        confluence_url = urlparse(uri).netloc

        # Extract space key from the URI
        path_parts = urlparse(uri).path.split('/')
        space_key = path_parts[3]  # Assuming standard format with '/wiki/spaces/{space_key}/...'

        # Fetch all pages in the space
        pages = confluence.get_all_pages_from_space(space_key, start=0, limit=100, expand='body.storage', content_type='page')

        # Process each page
        for page in pages:
            page_id = page['id']
            title = page['title']
            text = page['body']['storage']['value']
            page_url = f"https://{confluence_url}/wiki/spaces/{space_key}/pages/{page_id}"

            content = f"Contents from confluence page: {page_url}"
            content += text
            content += f"Contents from confluence page: {page_url}"

            # Chunk and embed the content
            logger.info(f"Processing page: {title} ({page_url})")
            text_chunks = embedding_client.chunk_text(content)
            if quick and len(text_chunks) > 1:
                text_chunks = [text_chunks[0], text_chunks[-1]]

            chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                      for i, text in enumerate(text_chunks)]

            # Create Resource and insert into database
            resource = Resource(uri=page_url, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
            database_client.insert(resource)
