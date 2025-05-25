 `vault`
A CLI tool for local embedding storage and search.

## Setup
### Installation
```bash
uv tool install git+https://github.com/WillChangeThisLater/vault
```

### Upgrade
```bash
uv tool upgrade vault
```

## Why `vault`?
- Simplicity: `vault` has a dead simple CLI
  ```bash
  # clear the vault
  vault delete *
  # add all files in current directory ending in '.txt'
  vault add *.txt
  # make sure all your files are added
  vault ls
  # search for something!
  vault search "romeo and juliet"
  # delete all the text files
  vault delete *.txt
  ```
- Flexibility: `vault` supports multiple types of resources
    - Text files (e.g. file.txt)
    - Image files (e.g. image.jpg)
    - Web links (e.g. https://www.example.com)
    - Directories (e.g. /path/to/project)
- Privacy focused: `vault` never stores data directly. It only stores pointers to the resources you add.

## Roadmap
### Easy
- Support different output formats
- Support more resource types (slack links, github links, etc.)
- Refactor services.py to split out resource handlers into separate modules

### Hard
- MCP support
- Video resources (transcripts + frames)
- Browser extension

## Agentic
- Research a service. This agent responds to a specific URI pattern.
  The agent would probably:
    - Search github/slack/confluence for documentation 
    - Read the README
    - Dynamically find important files (clone the repo + use unix tools?)
