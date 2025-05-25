import logging
import requests
import io
from bs4 import BeautifulSoup  # For scraping and parsing HTML content
from playwright.sync_api import sync_playwright
from PIL import Image  # For image processing

from urllib.parse import urlparse
from vault.plugins.base_plugin import BasePlugin
from vault.models import Resource, Chunk
from vault.clients.embedding_clients.base import BaseEmbeddingClient
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.clients.llm_clients.base import BaseLLMClient

logger = logging.getLogger(__name__)

class WebPlugin(BasePlugin):

    def can_handle(self, uri: str):
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _fetch_from_url(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _screenshot_website(self, url: str) -> Image:
        # Initialize Playwright
        with sync_playwright() as p:
            # Launch a browser instance
            browser = p.chromium.launch()
            # Open a new page
            page = browser.new_page()
            # Navigate to the given URL
            page.goto(url)
            # Take a full-page screenshot
            screenshot_bytes = page.screenshot(full_page=True)
            # Close browser
            browser.close()
    
            # Load the screenshot bytes into a Pillow image
            image = Image.open(io.BytesIO(screenshot_bytes))
    
        return image

    def handle(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        html_content = self._fetch_from_url(uri)
        soup = BeautifulSoup(html_content, "html.parser")
        text_content = soup.get_text()
        text_chunks = embedding_client.chunk_text(text_content)

        # Create chunks from text
        if quick and len(text_chunks) > 1:
            text_chunks = [text_chunks[0], text_chunks[-1]]
        chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                                 for i, text in enumerate(text_chunks)]

        if not quick:
            # Example to include summarized image embedding
            prompt = """
            The image you are about to see is a full page screenshot from a website

            I want to include this screenshot as part of an embedding search engine I am making.
            The goal of this engine is to allow users to perform semantic search on text,
            images, and videos seamlessly.

            This poses a problem, however: image and text typically don't live in the same
            embedding space. To overcome this problem, I've opted to summarize images and
            embed their text summaries.

            Your job is to summarize the provided screenshot with the semantic search use case
            in mind. Think about the sort of queries to which this image would be an
            appropriate response; write your summary with these queries in mind.

            Be extremely verbose without being superfluous. Transcribe any and all written text in the image, verbatim.

            Once you have transcribed everything, comment on the following

                - Describe the overall content of the webpage. Who is it written for? What is it about?
                - Describe any images in the webpage in detail
                - Discuss the overall layout of the webpage. How is the page laid out visually? What colors does the website use?
                  Are there any notable landmarks or features?
            """
            try:
                image = self._screenshot_website(uri)
                description = llm_client.summarize_image(image, prompt)
                image_embedding_chunk = Chunk(index=0, embedding=embedding_client.generate_embedding(description), type="image")
                chunks += [image_embedding_chunk]
            except Exception as e:
                logger.warning(f"Could not summarize screenshot from website {uri} - {e}. Skipping")

        # Dummy hash logic
        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)
