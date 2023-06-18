"""Backup and Restore CLI."""
import click
import json
from typing import Optional
from homelab_node_red_backup.handler.backup import create_backup
from homelab_node_red_backup.handler.check import data_exists
from homelab_node_red_backup.handler.restore import restore_backup
from homelab_node_red_backup.handler.flows import get_flows


@click.group(chain=True)
def main():
    """CLI Entrypoint"""
    pass


@main.command(help="Checks if data exists. Return code is not 0 if no data exists!")
@click.option("--endpoint", "-e", type=str, required=True, help="Node-RED endpoint")
@click.option(
    "--jwt-token", "-jwt", type=str, required=False, help="JWT Token for authentication"
)
def check(endpoint: str, jwt_token: Optional[str]):
    click.echo(
        f"Using {endpoint} to check for Node-RED configuration "
        + f"(JWT enabled: {jwt_token != None})."
    )

    checkpoint = data_exists(endpoint, jwt_token)
    click.echo(f"Data exists: {checkpoint}")
    exit(not checkpoint)


@main.command(help="Backups the flows to the given file.")
@click.option("--endpoint", "-e", type=str, required=True, help="Node-RED endpoint")
@click.option("--file", "-f", type=str, required=True, help="Output JSON file")
@click.option(
    "--jwt-token", "-jwt", type=str, required=False, help="JWT Token for authentication"
)
def backup(endpoint: str, file: str, jwt_token: Optional[str]):
    click.echo(
        f"Using {endpoint} to backup Node-RED configuration to {file} "
        + f"(JWT enabled: {jwt_token != None})."
    )

    backup = create_backup(endpoint, jwt_token)
    with open(file, "w") as outfile:
        json.dump(backup, outfile, indent=2)
    click.echo("Backup created successfully.")


@main.command(help="Restores flows from the given file.")
@click.option("--endpoint", "-e", type=str, required=True, help="Node-RED endpoint")
@click.option("--file", "-f", type=str, required=True, help="Output JSON file")
@click.option(
    "--jwt-token", "-jwt", type=str, required=False, help="JWT Token for authentication"
)
def restore(endpoint: str, file: str, jwt_token: Optional[str]):
    click.echo(
        f"Using {endpoint} to restore {file} to Node-RED "
        + f"(JWT enabled: {jwt_token != None})."
    )

    with open(file, "r") as backup:
        restore_backup(endpoint, jwt_token, json.load(backup))
    click.echo("Restored backup successfully.")


@main.command(
    help="Backups to or restores from the given file depending on whether data exists."
)
@click.option("--endpoint", "-e", type=str, required=True, help="Node-RED endpoint")
@click.option("--file", "-f", type=str, required=True, help="Output JSON file")
@click.option(
    "--jwt-token", "-jwt", type=str, required=False, help="JWT Token for authentication"
)
def auto(endpoint: str, file: str, jwt_token: Optional[str]):
    click.echo(
        f"Using {endpoint} to auto backup/restore from/to {file} from/to Node-RED "
        + f"(JWT enabled: {jwt_token != None})."
    )

    flows = get_flows(endpoint, jwt_token)
    if data_exists(endpoint, jwt_token, flows):
        create_backup(endpoint, jwt_token, flows)
        click.echo("Created backup successfully.")
    else:
        with open(file, "r") as backup:
            restore_backup(endpoint, jwt_token, json.load(backup))
        click.echo("Restored backup successfully.")


if __name__ == "__main__":
    main()
