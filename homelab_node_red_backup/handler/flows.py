"""Backup Handler."""

import click
import requests
from requests.exceptions import RequestException

DEFAULT_TIMEOUT = 30


def get_flows(endpoint: str, jwt_token: str | None) -> dict:
    """Gets the existing flows and normalizes output to {'flows': [...]}.

    Node-RED may return either a list of flows or a dict with key 'flows'.
    This function ensures callers always get a dict with 'flows'.
    """
    headers = {"Node-RED-API-Version": "v2"}
    if jwt_token is not None:
        headers["Authorization"] = f"Bearer {jwt_token}"
    try:
        flows_request = requests.get(
            f"{endpoint}/flows/", headers=headers, timeout=DEFAULT_TIMEOUT
        )
        if not flows_request.ok:
            click.echo(
                f"Could not get flows from Node-RED: {flows_request.status_code}, "
                + f"{flows_request.text}"
            )
            raise click.Abort()
        try:
            data = flows_request.json()
        except ValueError as err:
            click.echo(f"Invalid JSON from Node-RED flows endpoint: {err}")
            raise click.Abort()
        if isinstance(data, list):
            return {"flows": data}
        if (
            isinstance(data, dict)
            and "flows" in data
            and isinstance(data["flows"], list)
        ):
            return data
        click.echo("Unexpected flows data format from Node-RED")
        raise click.Abort()
    except RequestException as err:
        click.echo(f"Error performing request to Node-RED: {err}")
        raise click.Abort()
