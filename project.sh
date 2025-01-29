#!/bin/bash

cat <<'EOF'
I want to write a tiny CLI tool, `vault`, for securely
saving scripts and repositories that contain sensitive information

For some background: often, I find myself writing scripts
that contain sensitive information (hardcoded API keys and
URLs, plaintext passwords, that sort of thing). I hate
having these just sitting on my system without any
encryption, but the scripts are dirty and useful.
I need a way to quickly and easily save these scripts
to a common place so I can find them again if I need them

How I envision the CLI:

```bash
> vault create          # create the vault: set storage location (should have reasonable default), decryption key (should be able to auto generate and save somewhere)
> vault list            # lists all the scripts currently stored in vault
> vault write script.py # store script.py in the vault
> vault read script.py  # reads script.py from the vault to stdout
> vault rm script.py    # deletes script.py from the vault
> vault search <>       # less essential feature. search for a script based on description
> vault destroy <>      # deletes everything in the vault

On the backend, there should be some database that maintains the scripts.
The database should be encrypted at rest. The `vault` command should
need to provide a decryption key every time it reads from the database.

For now, I envision `vault` as something of a singleton. It shouldn't
be 

Write `vault`. Use python.
```
EOF
