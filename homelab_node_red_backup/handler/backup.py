"""Backup Handler."""
import os
import requests
from homelab_node_red_backup.handler.flows import get_flows
from typing import Optional, List
import click
from requests.exceptions import RequestException

# Credential node types configurable via environment variable CREDENTIAL_NODES
# Format: comma-separated values, e.g. "server,telegram bot"
_default_credential_nodes = ["server", "telegram bot"]


def get_credential_nodes() -> List[str]:
    """Return credential node types from environment or defaults.

    Reads CREDENTIAL_NODES on each call so tests can change the env without
    requiring module reloads.
    """
    _env = os.getenv("CREDENTIAL_NODES")
    if _env:
        return [part.strip() for part in _env.split(",") if part.strip()]
    return _default_credential_nodes


def create_backup(
    endpoint: str, jwt_token: Optional[str], flows: dict | list | None = None
) -> dict:
    """Creates a backup JSON.

    The `flows` parameter accepts either a dict (expected shape {'flows': [...]}) or a
    list of flows; lists are normalized to {'flows': [...]}.
    """
    try:
        fetched_flows = flows if flows is not None else get_flows(endpoint, jwt_token)
        if isinstance(fetched_flows, list):
            fetched_flows = {"flows": fetched_flows}
        if not isinstance(fetched_flows, dict):
            click.echo("Invalid flows format received from Node-RED")
            raise click.Abort()
        if "flows" not in fetched_flows or not isinstance(fetched_flows["flows"], list):
            click.echo("Invalid flows format received from Node-RED")
            raise click.Abort()
        credentials = _get_credentials(endpoint, jwt_token, fetched_flows)
        return {
            "flows": fetched_flows["flows"],
            "credentials": credentials,
        }
    except RequestException as error:
        click.echo(f"Network error when accessing Node-RED: {error}")
        raise click.Abort()
    except click.Abort:
        # intentional aborts should propagate unchanged
        raise
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()


def _get_credentials(endpoint: str, jwt_token: Optional[str], flows: dict) -> dict:
    """Gets the credentials for flows.

    Validates that nodes which require credentials contain both 'id' and 'type'. If a
    credential node is missing an 'id' or 'type', abort with a clear message to
    avoid malformed requests or storing under a None key.
    """
    nodes = []
    for node in flows.get("flows", []):
        if not isinstance(node, dict):
            click.echo(f"Invalid flow node format received from Node-RED: {node}")
            raise click.Abort()
        node_type = node.get("type")
        node_id = node.get("id")
        if node_type in get_credential_nodes():
            if not node_type or not node_id:
                click.echo(f"Flow node missing 'id' or 'type' for credential lookup: {node}")
                raise click.Abort()
            nodes.append({"id": node_id, "type": node_type})
    try:
        headers = {}
        if jwt_token is not None:
            headers["Authorization"] = f"Bearer {jwt_token}"
        credentials = {}
        for node in nodes:
            url = (
                f"{endpoint}/credentials/"
                + f"{node['type'].replace(' ', '-')}/"
                + f"{node['id']}"
            )
            resp = requests.get(url, headers=headers)
            if not resp.ok:
                click.echo(
                    f"Could not get credentials for node {node['id']}: {resp.status_code}, {resp.text}"
                )
                raise click.Abort()
            try:
                credentials[node["id"]] = resp.json()
            except ValueError as err:
                click.echo(f"Invalid JSON when fetching credentials for node {node['id']}: {err}")
                raise click.Abort()
        return credentials
    except RequestException as err:
        click.echo(f"Error performing request to Node-RED: {err}")
        raise click.Abort()
