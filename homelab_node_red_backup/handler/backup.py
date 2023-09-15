"""Backup Handler."""
import requests
from homelab_node_red_backup.handler.flows import get_flows
from typing import Optional
import click

CREDENTIAL_NODES = ["server", "telegram bot"]


def create_backup(
    endpoint: str, jwt_token: Optional[str], flows: Optional[dict] = None
) -> dict:
    """Creates a backup JSON."""
    try:
        fetched_flows = flows if flows is not None else get_flows(endpoint, jwt_token)
        credentials = _get_credentials(endpoint, jwt_token, fetched_flows)
        return {
            "flows": fetched_flows["flows"],
            "credentials": credentials,
        }
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()


def _get_credentials(endpoint: str, jwt_token: Optional[str], flows: dict) -> dict:
    """Gets the credentials for a flows."""
    nodes = [
        {"id": node["id"], "type": node["type"]}
        for node in filter(
            lambda node: node["type"] in CREDENTIAL_NODES, flows["flows"]
        )
    ]
    try:
        headers = {}
        if jwt_token is not None:
            headers["Authorization"] = f"Bearer {jwt_token}"
        return dict(
            [
                (
                    node["id"],
                    requests.get(
                        f"{endpoint}/credentials/"
                        + f"{node['type'].replace(' ', '-')}/"
                        + f"{node['id']}",
                        headers=headers,
                    ).json(),
                )
                for node in nodes
            ]
        )
    except Exception as err:
        click.echo(f"Error performing request to Node-RED: {err}")
        raise click.Abort()
