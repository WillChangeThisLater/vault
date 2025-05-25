import os
import re

def get_default_db_path():
    """Gets the default path for the DuckDB database."""
    home_directory = os.path.expanduser("~")
    return os.path.join(home_directory, "embeddings.db")


def filter_uris_by_regex(uris: list[str], pattern: str):
    """Filter list of URIs by some pattern"""
    return [uri for uri in uris if re.match(pattern, uri)]

def get_directory_tree(path: str) -> str:
    """Generate a text representation of the directory structure."""
    tree_lines = []
    for root, _, files in os.walk(path):
        level = root.replace(path, '').count(os.sep)
        indent = ' ' * 4 * level
        tree_lines.append(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            tree_lines.append(f'{sub_indent}{f}')
    return "\n".join(tree_lines)

def read_readme(path: str) -> str:
    """Read the README.md file from the directory."""
    readme_path = os.path.join(path, 'README.md')
    if os.path.isfile(readme_path):
        with open(readme_path, 'r') as file:
            return file.read()
    return ""
