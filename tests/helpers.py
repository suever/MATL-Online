"""Functions to be used across tests for convenience."""

from typing import Optional

from flask_socketio import SocketIOTestClient


def session_id_for_client(client: SocketIOTestClient, namespace: str = '/') -> Optional[str]:
    """Retrieve the session id for a SocketIOTestClient."""
    return client.socketio.server.manager.sid_from_eio_sid(client.eio_sid, namespace)
