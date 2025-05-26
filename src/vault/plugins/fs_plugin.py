import logging
import os
import pdf2image
import mimetypes
from PIL import Image  # For image processing

from vault.plugins.base_plugin import BasePlugin
from vault.models import Resource, Chunk
from vault.clients.embedding_clients.base import BaseEmbeddingClient
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.clients.llm_clients.base import BaseLLMClient
from vault.utils import get_directory_tree, read_readme

logger = logging.getLogger(__name__)

class TextFilePlugin(BasePlugin):

    def _determine_resource_type(self, uri: str) -> str:
        """Determine the type of the resource."""
        if os.path.isfile(uri):
            mime_type, _ = mimetypes.guess_type(uri)
            if mime_type and 'text' in mime_type:
                return "text"
            elif mime_type and 'image' in mime_type:
                return "image"
            elif mime_type == "application/pdf":
                return "pdf"
            # treat shell scripts as text
            elif mime_type == "application/x-sh":
                return "text"
            # treat json as text
            elif mime_type == "application/json":
                return "text"
            # if the mime type wasn't found, assume text
            elif not mime_type:
                return "text"
            else:
                logger.warning(f"Mime type {mime_type} not supported")
                return ""
        elif os.path.isdir(uri):
            return "dir"
        else:
            logger.info(f"URI {uri} not recognized")
            return ""

    def can_handle(self, uri: str) -> bool:
        return bool(self._determine_resource_type(uri))

    def handle(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        resource_type = self._determine_resource_type(uri)
        if resource_type == "text":
            self._handle_file(uri, embedding_client, database_client, quick)
        elif resource_type == "image":
            self._handle_image(uri, embedding_client, database_client, llm_client)
        elif resource_type == "pdf":
            self._handle_pdf(uri, embedding_client, database_client, llm_client)
        elif resource_type == "dir":
            self._handle_dir(uri, embedding_client, database_client, llm_client, quick)
        else:
            raise NotImplementedError(f"File system plugin client does not understand resource type '{resource_type}'")

    def _handle_file(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, quick: bool = False):
        uri = os.path.abspath(os.path.expanduser(uri))
        with open(uri, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # cut down on # of chunks if user just wants a quick embedding
        text_chunks = embedding_client.chunk_text(content)
        if quick and len(text_chunks) > 1:
            text_chunks = [text_chunks[0], text_chunks[-1]]

        chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                  for i, text in enumerate(text_chunks)]
        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)

    def _handle_image(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient):
        uri = os.path.abspath(os.path.expanduser(uri))
        # generate a textual description of the image
        image = Image.open(uri)
        prompt = """
        The image you are about to see is from my local file system.

        I want to include this image as part of an embedding search engine I am making.
        The goal of this engine is to allow users to perform semantic search on text,
        images, and videos seamlessly.

        This poses a problem, however: image and text typically don't live in the same
        embedding space. To overcome this problem, I've opted to summarize images and
        embed their text summaries.

        Your job is to summarize the provided image with the semantic search use case
        in mind. Think about the sort of queries to which this image would be an
        appropriate response; write your summary with these queries in mind.

        Some examples of things you should include:

            - Transcribe any written text in the image, verbatim
            - Describe people, places, and things in as much detail as possible
            - If you recognize the image (e.g. if it is of the NYC skyline, was painted
              by Van Gogh, etc) provide that context as well!
        """
        description = llm_client.summarize_image(image, prompt)
        logger.info(f"Image summary: {description}")

        # embed the description
        chunks = [Chunk(index=0, embedding=embedding_client.generate_embedding(description), type="image")]
        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)

    def _handle_pdf(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient):

        uri = os.path.abspath(os.path.expanduser(uri))
        images = pdf2image.convert_from_path(uri)
        chunks = []
        for i, image in enumerate(images):
            # generate a textual description of the image
            prompt = """
            The image you are about to see is a page from a PDF on my local file system.

            I want to include this page as part of an embedding search engine I am making.
            The goal of this engine is to allow users to perform semantic search on text,
            images, and videos seamlessly.

            This poses a problem, however: image and text typically don't live in the same
            embedding space. So I want to convert this image to a text representation.

            Your job is to transcribe all the text on the page, verbatim.
            Also describe interesting images/landmarks, if and when they appear on the page
            """

            # Conver the image to JPEG before summarizing
            image = image.convert("RGB")
            image.format = "JPEG"
            description = llm_client.summarize_image(image, prompt)
            logger.info(f"PDF page {i} summary: {description}")

            # embed the description
            chunks.append(Chunk(index=i, embedding=embedding_client.generate_embedding(description), type="image"))

        if not chunks:
            raise ValueError(f"No chunks from PDF {uri} found")

        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)

    def _handle_dir(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        """Process a directory"""
        uri = os.path.abspath(os.path.expanduser(uri))
        project_name = os.path.split(uri)[-1]
        tree = get_directory_tree(uri)
        readme = read_readme(uri)
        if not readme:
            readme = "No README found"

        prompt = f"""
        The information you are about to see is from a project

        I want to include this project as part of an embedding search engine I am making.
        The goal of this engine is to allow users to perform semantic search on text.

        This poses a problem, however: projects contain a number of files, and it can
        be difficult (and expensive!) to describe a project by just embedding each of
        its files individually.

        To solve this problem, I've opted to provide the project name, directory tree,
        and README. Your job is to summarize this information in a descriptive, useful
        way without being too superfluous. Information about the project is below:

        Project Name: {project_name}
        Directory: {uri}
        Project tree: {tree}
        README: {readme}
        """


        summary = llm_client.summarize(prompt)
        logger.info(f"Summary for project {project_name}: {summary}")

        text_chunks = embedding_client.chunk_text(summary)
        if quick and len(text_chunks) > 1:
            text_chunks = [text_chunks[0], text_chunks[-1]]

        chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                  for i, text in enumerate(text_chunks)]
        if len(chunks) > 1:
            logger.warning(f"Directory summary expressed in more than one chunk {uri}. This could result in accuracy loss")

        # Dummy hash logic
        resource = Resource(uri=uri, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
        database_client.insert(resource)
