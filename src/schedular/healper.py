import inngest
from typing import Any
from .client import inngest_client


def trigger_inngest_events(name: str, data: Any | None = ..., id: str | None = None):
    return inngest_client.send_sync(inngest.Event(name=name, data=data, id=id))
