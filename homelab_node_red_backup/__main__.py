"""Backup and Restore CLI."""

import json
import sys

import click

from homelab_node_red_backup.handler.backup import create_backup
from homelab_node_red_backup.handler.check import data_exists
from homelab_node_red_backup.handler.flows import get_flows
from homelab_node_red_backup.handler.restore import restore_backup


@click.group(chain=True)
def main():
    """CLI Entrypoint"""


def common_options(func):
    """Decorator to apply common endpoint and jwt-token CLI options."""
    func = click.option(
        "--jwt-token",
        "-jwt",
        type=str,
        required=False,
        help="JWT Token for authentication",
    )(func)
    func = click.option(
        "--endpoint", "-e", type=str, required=True, help="Node-RED endpoint"
    )(func)
    return func


def file_option(help_text: str):
    """Decorator to apply file option."""
    return click.option("--file", "-f", type=str, required=True, help=help_text)


@main.command(help="Checks if data exists. Return code is not 0 if no data exists!")
@common_options
def check(endpoint: str, jwt_token: str | None):
    click.echo(
        f"Using {endpoint} to check for Node-RED configuration "
        + f"(JWT enabled: {jwt_token is not None})."
    )

    checkpoint = data_exists(endpoint, jwt_token)
    click.echo(f"Data exists: {checkpoint}")
    sys.exit(not checkpoint)


@main.command(help="Backups the flows to the given file.")
@common_options
@file_option("Output JSON file")
def backup(endpoint: str, file: str, jwt_token: str | None):
    click.echo(
        f"Using {endpoint} to backup Node-RED configuration to {file} "
        + f"(JWT enabled: {jwt_token is not None})."
    )

    backup_data = create_backup(endpoint, jwt_token)
    with open(file, "w") as outfile:
        json.dump(backup_data, outfile, indent=2)
    click.echo("Backup created successfully.")


@main.command(help="Restores flows from the given file.")
@common_options
@file_option("Input JSON file")
def restore(endpoint: str, file: str, jwt_token: str | None):
    click.echo(
        f"Using {endpoint} to restore {file} to Node-RED "
        + f"(JWT enabled: {jwt_token is not None})."
    )

    with open(file, "r") as backup:
        restore_backup(endpoint, jwt_token, json.load(backup))
    click.echo("Restored backup successfully.")


@main.command(
    help="Backups to or restores from the given file depending on whether data exists."
)
@common_options
@file_option("Output/Input JSON file")
def auto(endpoint: str, file: str, jwt_token: str | None):
    click.echo(
        f"Using {endpoint} to auto backup/restore from/to {file} from/to Node-RED "
        + f"(JWT enabled: {jwt_token is not None})."
    )

    flows = get_flows(endpoint, jwt_token)
    if data_exists(endpoint, jwt_token, flows):
        backup_data = create_backup(endpoint, jwt_token, flows)
        with open(file, "w") as outfile:
            json.dump(backup_data, outfile, indent=2)
        click.echo("Created backup successfully.")
    else:
        with open(file, "r") as backup:
            restore_backup(endpoint, jwt_token, json.load(backup))
        click.echo("Restored backup successfully.")


if __name__ == "__main__":
    main()
