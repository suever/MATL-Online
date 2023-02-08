"""Functions to be used across tests for convenience."""

from typing import Optional

from flask_socketio import SocketIOTestClient  # type: ignore


def session_id_for_client(
    client: SocketIOTestClient, namespace: str = "/"
) -> Optional[str]:
    """Retrieve the session id for a SocketIOTestClient."""
    session_id: Optional[str] = client.socketio.server.manager.sid_from_eio_sid(
        client.eio_sid, namespace
    )

    return session_id
