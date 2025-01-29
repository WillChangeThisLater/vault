#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
#   "cryptography",
# ]
# ///
import os
import click
import sqlite3
from cryptography.fernet import Fernet

# Constants for paths
DB_PATH = os.path.expanduser("~/.vault/vault.db")
KEY_PATH = os.path.expanduser("~/.vault/.key")


def ensure_db_and_key_exist():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("CREATE TABLE scripts (name TEXT PRIMARY KEY, content BLOB)")
        conn.close()

    if not os.path.exists(KEY_PATH):
        with open(KEY_PATH, 'wb') as key_file:
            key_file.write(Fernet.generate_key())


def load_key():
    print(KEY_PATH)
    with open(KEY_PATH, 'rb') as key_file:
        return key_file.read()


def encrypt(content, key):
    f = Fernet(key)
    return f.encrypt(content.encode('utf-8'))


def decrypt(encrypted_content, key):
    f = Fernet(key)
    return f.decrypt(encrypted_content).decode('utf-8')


@click.group()
def vault():
    """A CLI tool for securely saving scripts and repositories."""
    ensure_db_and_key_exist()


@vault.command()
def create():
    """Create the vault."""
    ensure_db_and_key_exist()
    click.echo("Vault has been created and is ready to use.")


@vault.command()
def ls():
    """List all stored scripts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM scripts")
    scripts = [row[0] for row in cursor.fetchall()]
    conn.close()
    click.echo("\n".join(scripts))


@vault.command()
@click.argument('filename')
def store(filename):
    """Store a script in the vault."""
    with open(filename, 'r') as file:
        content = file.read()

    key = load_key()
    encrypted_content = encrypt(content, key)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO scripts (name, content) VALUES (?, ?)", (filename, encrypted_content))
    conn.commit()
    conn.close()
    click.echo(f"{filename} has been stored in the vault.")


@vault.command(name="open")
@click.argument('filename')
def open_file(filename):
    """Read a script from the vault to stdout."""
    key = load_key()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT content FROM scripts WHERE name=?", (filename,))
    result = cursor.fetchone()
    conn.close()

    if result:
        decrypted_content = decrypt(result[0], key)
        click.echo(decrypted_content)
    else:
        click.echo(f"{filename} not found in the vault.")


@vault.command()
@click.argument('filename')
def rm(filename):
    """Delete a script from the vault."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM scripts WHERE name=?", (filename,))
    conn.commit()
    conn.close()
    click.echo(f"{filename} has been removed from the vault.")


@vault.command()
def destroy():
    """Delete everything in the vault."""
    if click.confirm("Are you sure you want to completely destroy the vault? This action cannot be undone."):
        os.remove(DB_PATH)
        os.remove(KEY_PATH)
        click.echo("Vault destroyed.")


if __name__ == "__main__":
    vault()

