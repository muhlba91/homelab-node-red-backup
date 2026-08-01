"""Restore Handler."""
import json

import click
import requests
from requests.exceptions import RequestException


def restore_backup(endpoint: str, jwt_token: str | None, flows: str | dict | list) -> None:
    """Restores from a backup.

    `flows` may be provided as a dict or list (already parsed), or as a JSON string
    containing an object/array. The function validates the payload and posts it to
    Node-RED's /flows/ endpoint.
    """
    headers = {"Node-RED-API-Version": "v2", "Node-RED-Deployment-Type": "full"}
    if jwt_token is not None:
        headers["Authorization"] = f"Bearer {jwt_token}"
    try:
        try:
            json_payload = flows if isinstance(flows, (dict, list)) else json.loads(flows)
        except (TypeError, json.JSONDecodeError):
            click.echo("Provided flows payload is not valid JSON or serializable")
            raise click.Abort()
        if not isinstance(json_payload, (dict, list)):
            click.echo("Provided flows payload must be a JSON object or array")
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
    except click.Abort:
        # intentional aborts should propagate unchanged
        raise
    except Exception as error:  # noqa: BLE001
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()
