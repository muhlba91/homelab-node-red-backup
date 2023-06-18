"""Check Handler."""
from homelab_node_red_backup.handler.flows import get_flows
from typing import Optional
import click


def data_exists(endpoint: str, jwt_token: Optional[str]) -> bool:
    """Checks if data exists."""
    try:
        flows = get_flows(endpoint, jwt_token)
        return len(flows["flows"]) > 0
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()
