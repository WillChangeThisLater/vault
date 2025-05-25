#!/bin/bash

set -euo pipefail

reference_links=(
  # duckdb
  "https://blog.brunk.io/posts/similarity-search-with-duckdb/" "https://duckdb.org/2024/05/03/vector-similarity-search-vss.html"
  "https://motherduck.com/blog/search-using-duckdb-part-1/"
  "https://duckdb.org/docs/stable/sql/data_types/array"
  "https://duckdb.org/docs/stable/sql/functions/array.html"
  "https://click.palletsprojects.com/en/stable/"
  # uv
  "https://docs.astral.sh/uv/concepts/projects/init/"
  "https://docs.astral.sh/uv/guides/projects/"
  # bedrock converse API stuff
  # i want the LLM to use this to generate image summarizer
  "https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html"
  "https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Message.html"
  "https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ContentBlock.html"
  "https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ImageBlock.html"
  "https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ImageSource.html"
  "https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-examples.html"
  # I want the LLM to write the screenshoting code
  "https://playwright.dev/python/docs/screenshots"
)

reference_links=(
  "https://atlassian-python-api.readthedocs.io/"
  "https://atlassian-python-api.readthedocs.io/confluence.html#get-page-info"
  "https://atlassian-python-api.readthedocs.io/jira.html"
)

# Function to display references in a readable manner
references() {
  echo "# Reference Index"
  for reference_link in "${reference_links[@]}"; do
    # Print a header with Markdown style
    echo -e "\n## Reference: $reference_link\n"
    lynx -dump -nolist "$reference_link"
    echo -e "\n"
  done
}

run() {

    # remove the embeddings DB file if it already exists
    if [ -f "file_to_remove" ]; then
      rm "embeddings.db"
    fi

    echo "$@" >&2

    echo "\`\`\`bash"
    echo "\$ $@"
    $@ 2>&1
    echo "\`\`\`"
}

about() {
	cat <<EOF
Vault is a CLI tool for performing embedding and vector search locally.

Here is the current directory structure:

\`\`\`bash
$(tree)
\`\`\`

And here are the current contents of the project (ignoring prompt.sh,
which is used to define this prompt):

$(files-to-prompt . --ignore "prompt.sh" --ignore "embeddings.db" --ignore "uv.lock" --ignore "data" 2>/dev/null)

This project writes to a parquet file on the backend.
The schema of this parquet file is defined below:

\`\`\`schema
- embedding_id: A unique identifier for each embedding.
- source: The original source path or URL. This could be a file path for local files or a URL for web input.
- source_hash: A hash of the content (e.g., SHA256) to detect changes in the source content for URL-based or local file inputs.
- chunk_index: The index of the chunk in the source file. Helps in reconstructing the original document if needed.
- embedding: The embedding vector itself. The size will depend on the embedding model used.
- model_id: Identifier or name of the model used to generate the embedding.
- created_at: Record of when the embedding was created.
\`\`\`
EOF
}

misc() {
	cat <<EOF
What I want to understand is: what should my data model look like?
There are a few things to keep in mind here:

	(1) Chunking. I won't be able to embed a huge file; I'll have
	    to split it up into multiple chunks and embed each separately

	(2) I'm running this locally, using local files. I don't think
	    I'll actually want to store the file inside the database
		itself; I'll just want to store the embedding.

		This probably implies some kind of cleanup procedure at some point,
		where 'vault' finds files that have updated last modified dates
		(or just don't exist anymore) and does something with them.
		But worry about this later.

	(3) I might need to support multiple embedding models in the future
	    At the very least there should be a model field indicating what
		model was used to generate an embedding

	(4) Eventually, I'll probably want \`vault\` to support URL inputs (so the tool will
	    have to be able to work with these too). It'll be harder to detect
		changes on these - maybe a content hash here is appropriate?

Suggest a coherent set of table(s) that will accomplish this goal while
keeping \`vault\` simple. The fewer tables the better. 

EOF
}

roadmap() {
  cat <<EOF
# Roadmap
- (DONE) Add directory support (use directory summary w/ tree, README, etc and get LLM to summarize)
- (DONE) Add multiple resources: 'vault add a.txt b.txt c.txt'
- (DONE) Delete multiple resources with regex support: 'vault delete *.txt'
- Async?
- More/better output formats
  - CSV, JSON
- Custom integrations
  - Slack
  - Github
- Video support
  - Transcribe videos to get text
  - Sample video frames to show images
- Tests
- Refactor service.py module
- Highlighting relevant results? Though this might imply TUI...
- Site scraping capabilities? Maybe with LLM support to only grab important pages?
- TUI?
- Async?
EOF
}


example() {
  cat <<'EOF'
import logging
import os
from urllib.parse import urlparse
from vault.plugins.base_plugin import BasePlugin
from vault.models import Resource, Chunk
from vault.clients.embedding_clients.base import BaseEmbeddingClient
from vault.clients.database_clients.base import BaseDatabaseClient
from vault.clients.llm_clients.base import BaseLLMClient
from atlassian import Confluence

logger = logging.getLogger(__name__)

class ConfluencePlugin(BasePlugin):

    def can_handle(self, uri: str) -> bool:
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc, '/wiki/spaces/' in result.path])
        except ValueError:
            return False

    def handle(self, uri: str, embedding_client: BaseEmbeddingClient, database_client: BaseDatabaseClient, llm_client: BaseLLMClient, quick: bool = False):
        # Extract Confluence credentials from the URI or environment variables
        confluence_url = urlparse(uri).netloc
        username, password = os.environ["CONFLUENCE_API_USERNAME"], os.environ["CONFLUENCE_API_KEY"]

        # Initialize Confluence client
        confluence = Confluence(
            url=f'https://{confluence_url}',
            username=username,
            password=password,
            cloud=True
        )

        # Extract space key from the URI
        path_parts = urlparse(uri).path.split('/')
        space_key = path_parts[3]  # Assuming standard format with '/wiki/spaces/{space_key}/...'

        # Fetch all pages in the space
        pages = confluence.get_all_pages_from_space(space_key, start=0, limit=100, expand='body.storage', content_type='page')

        # Process each page
        for page in pages:
            content = page['body']['storage']['value']
            page_id = page['id']
            title = page['title']
            page_url = f"https://{confluence_url}/wiki/spaces/{space_key}/pages/{page_id}"

            logger.info(f"Processing page: {title} ({page_url})")

            # Chunk and embed the content
            text_chunks = embedding_client.chunk_text(content)
            if quick and len(text_chunks) > 1:
                text_chunks = [text_chunks[0], text_chunks[-1]]

            chunks = [Chunk(index=i, embedding=embedding_client.generate_embedding(text), type="text")
                      for i, text in enumerate(text_chunks)]

            # Create Resource and insert into database
            resource = Resource(uri=page_url, hash="dummy_hash", model_id=embedding_client.model_id, chunks=chunks)
            database_client.insert(resource)
EOF
}

main() {
	cat <<EOF
I am building a python based CLI tool, 'vault', for semantic search.

About \`vault\`:
$(about)

Roadmap for \`vault\`:
$(roadmap)

Modify the confluence plugin to handle JIRA tickets like the following:

  https://company.atlassian.net/browse/BIE-3111

When the plugin sees a JIRA ticket, it should gather the ticket description,
status, requester/doers, summary, comments, etc. and put that all into
one big description. The more metadata the better

References:
$(references)

EOF

}

main
