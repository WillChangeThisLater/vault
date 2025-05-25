#!/bin/bash

reindex() {
  for file in $(find data/samples -type f); do
    echo "Adding file $file to vault"
    uv run vault-v2 add "$file"
  done
}

reindex
uv run vault-v2 search "god is dead"
