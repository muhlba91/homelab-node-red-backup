"""Check Handler."""
from homelab_node_red_backup.handler.flows import get_flows
from typing import Optional
import click
from requests.exceptions import RequestException


def data_exists(
    endpoint: str, jwt_token: Optional[str], flows: Optional[dict] = None
) -> bool:
    """Checks if data exists.

    Validates that the fetched payload is a dict with a 'flows' key and that
    'flows' is a list before inspecting its length.
    """
    try:
        fetched_flows = flows if flows is not None else get_flows(endpoint, jwt_token)
        if not isinstance(fetched_flows, dict) or "flows" not in fetched_flows:
            click.echo("Invalid flows format received from Node-RED")
            raise click.Abort()
        if not isinstance(fetched_flows["flows"], list):
            click.echo("Invalid flows format received from Node-RED")
            raise click.Abort()
        return len(fetched_flows["flows"]) > 0
    except RequestException as error:
        click.echo(f"Network error when accessing Node-RED: {error}")
        raise click.Abort()
    except click.Abort:
        # intentional aborts should propagate unchanged
        raise
    except Exception as error:
        click.echo(f"Could not make request to Node-RED: {error}")
        raise click.Abort()
