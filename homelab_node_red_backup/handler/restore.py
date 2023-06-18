"""Restore Handler."""
import requests
from typing import Optional
import click


def restore_backup(endpoint: str, jwt_token: Optional[str], flows: str):
    """Restores from a backup."""
    headers = {"Node-RED-API-Version": "v2", "Node-RED-Deployment-Type": "full"}
    if jwt_token is not None:
        headers["Authorization"] = f"Bearer {jwt_token}"
    try:
        request = requests.post(f"{endpoint}/flows/", json=flows, headers=headers)
        if not request.ok:
            click.echo(
                f"Could not push flows to Node-RED: {request.status_code}, "
                + f"{request.text}"
            )
            raise click.Abort()
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()
