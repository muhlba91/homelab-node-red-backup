"""Backup Handler."""
import os
import requests
from homelab_node_red_backup.handler.flows import get_flows
from typing import Optional, List
import click
import json
from requests.exceptions import RequestException

# Credential node types configurable via environment variable CREDENTIAL_NODES
# Format: comma-separated values, e.g. "server,telegram bot"
_default_credential_nodes = ["server", "telegram bot"]
_env = os.getenv("CREDENTIAL_NODES")
if _env:
    CREDENTIAL_NODES: List[str] = [part.strip() for part in _env.split(",") if part.strip()]
else:
    CREDENTIAL_NODES = _default_credential_nodes


def create_backup(
    endpoint: str, jwt_token: Optional[str], flows: Optional[dict] = None
) -> dict:
    """Creates a backup JSON."""
    try:
        fetched_flows = flows if flows is not None else get_flows(endpoint, jwt_token)
        if isinstance(fetched_flows, list):
            fetched_flows = {"flows": fetched_flows}
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
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()


def _get_credentials(endpoint: str, jwt_token: Optional[str], flows: dict) -> dict:
    """Gets the credentials for flows."""
    nodes = []
    for node in flows.get("flows", []):
        if node.get("type") in CREDENTIAL_NODES:
            nodes.append({"id": node.get("id"), "type": node.get("type")})
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
            except json.JSONDecodeError as err:
                click.echo(f"Invalid JSON when fetching credentials for node {node['id']}: {err}")
                raise click.Abort()
        return credentials
    except RequestException as err:
        click.echo(f"Error performing request to Node-RED: {err}")
        raise click.Abort()
