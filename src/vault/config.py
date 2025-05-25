import os
import yaml

DEFAULT_CONFIG = {
    "default": {
        "embedding_provider": "openai",
        "llm_provider": "openai",
        "database_provider": "duckdb"
    },
    "embedding_clients": {
        "openai": {
            "model_id": "text-embedding-3-large"
        },
        "bedrock": {
            "model_id": "amazon.titan-embed-text-v2:0"
        }
    },
    "llm_clients": {
        "openai": {
            "model_id": "gpt-4o-mini"
        },
        "bedrock": {
            "model_id": "amazon.nova-pro-v1:0"
        }
    },
    # not currently used
    "database_clients": {
        "duckdb": {
            "db_path": "~/embeddings.db"
        }
    }
}

def load_config():
    config_path = os.path.expanduser("~/.config/vault.yaml")
    # Check if the config file exists
    if not os.path.exists(config_path):
        # Create default config if not exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as file:
            yaml.dump(DEFAULT_CONFIG, file)
        print(f"Default configuration created at {config_path}.")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config
