## Background
I sometimes hardcode credentials (api keys, passwords, etc.) into my scripts.

Most of these scripts are one off scripts that I use for debugging.
Normally I find myself throwing these scripts away (since they
have hardcoded credentials in them), only to need the script
again two weeks later.

`vault` helps solve this problem. It isn't perfect, but it
provides a way for me to save scripts on my local system
with some level of security

## Setup
1. Install `uv`
2. Link this file to your path (something like `ln -s /home/arch/vault/vault.py /usr/bin/vault`)
3. `vault create` to create the database and encryption/decryption key

## The CLI
```bash
[arch@archlinux vault]$ vault --help
Usage: vault [OPTIONS] COMMAND [ARGS]...

  A CLI tool for securely saving scripts and repositories.

Options:
  --help  Show this message and exit.

Commands:
  create   Create the vault.
  destroy  Delete everything in the vault.
  ls       List all stored scripts.
  open     Read a script from the vault to stdout.
  rm       Delete a script from the vault.
  store    Store a script in the vault.
```

## Example
```bash
[arch@archlinux vault]$ vault create
Vault has been created and is ready to use.
[arch@archlinux vault]$ vault store README.md
/home/arch/.vault/.key
README.md has been stored in the vault.
[arch@archlinux vault]$ vault store project.sh --description "prompt for building vault"
/home/arch/.vault/.key
project.sh has been stored in the vault.
[arch@archlinux vault]$ vault store vault.py --description "code for vault CLI tool"
/home/arch/.vault/.key
vault.py has been stored in the vault.
[arch@archlinux vault]$ vault ls
README.md: No description available
project.sh: prompt for building vault
vault.py: code for vault CLI tool
[arch@archlinux vault]$ vault destroy
Are you sure you want to completely destroy the vault? This action cannot be undone. [y/N]: y
Vault destroyed.
[arch@archlinux vault]$ vault ls
```
