"""This file contains the helper functions for the schedular."""

from typing import Any
import inngest
from .client import inngest_client


def trigger_inngest_events(
    name: str,
    data: Any | None = ...,
    # pylint: disable=redefined-builtin
    id: str | None = None,
    **fields
):
    """A helper function which abstracts the inngest configs from models"""
    return inngest_client.send_sync(
        inngest.Event(name=name, data=data, id=id, **fields)
    )
