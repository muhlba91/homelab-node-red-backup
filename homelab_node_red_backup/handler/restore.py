"""Restore Handler."""
import requests
from typing import Optional
import click
from requests.exceptions import RequestException
import json


def restore_backup(endpoint: str, jwt_token: Optional[str], flows: dict):
    """Restores from a backup. `flows` should be a dict or list that can be serialized to JSON."""
    headers = {"Node-RED-API-Version": "v2", "Node-RED-Deployment-Type": "full"}
    if jwt_token is not None:
        headers["Authorization"] = f"Bearer {jwt_token}"
    try:
        try:
            json_payload = flows if isinstance(flows, (dict, list)) else json.loads(flows)
        except (TypeError, json.JSONDecodeError):
            click.echo("Provided flows payload is not valid JSON or serializable")
            raise click.Abort()
        request = requests.post(f"{endpoint}/flows/", json=json_payload, headers=headers)
        if not request.ok:
            click.echo(
                f"Could not push flows to Node-RED: {request.status_code}, "
                + f"{request.text}"
            )
            raise click.Abort()
    except RequestException as error:
        click.echo(f"Network error when pushing flows to Node-RED: {error}")
        raise click.Abort()
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()
