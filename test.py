import sys
import json
from vault.clients.embedding_clients.bedrock import BedrockEmbeddingClient

def main():
    # Read input from stdin
    input_text = sys.stdin.read().strip()

    # Initialize the embedding client; use the same model ID as your main application
    model_id = "amazon.titan-embed-text-v2:0"
    embedding_client = BedrockEmbeddingClient(model_id)

    # Generate embedding for the input text
    embedding = embedding_client.generate_embedding(input_text)

    # Output the embedding as a JSON list of floats
    print(json.dumps(embedding))

if __name__ == "__main__":
    main()
