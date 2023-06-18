"""Backup Handler."""
import requests
from typing import Optional
import click


def get_flows(endpoint: str, jwt_token: Optional[str]) -> dict:
    """Gets the existing flows."""
    headers = {"Node-RED-API-Version": "v2"}
    if jwt_token is not None:
        headers["Authorization"] = f"Bearer {jwt_token}"
    try:
        flows_request = requests.get(f"{endpoint}/flows/", headers=headers)
        if not flows_request.ok:
            click.echo(
                f"Could not get flows from Node-RED: {flows_request.status_code}, "
                + f"{flows_request.text}"
            )
            raise click.Abort()
        return flows_request.json()
    except Exception as err:
        click.echo(f"Error performing request to Node-RED: {err}")
        raise click.Abort()
