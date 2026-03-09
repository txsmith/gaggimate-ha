"""GaggiMate WebSocket coordinator."""

import asyncio
import json
import logging
from typing import Any, Callable

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

RECONNECT_DELAY = 5  # seconds


class GaggiMateCoordinator:
    """Maintains a persistent WebSocket connection and pushes status updates to listeners."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self.hass = hass
        self.host = host
        self.data: dict[str, Any] = {}
        self._listeners: list[Callable[[], None]] = []
        self._task: asyncio.Task | None = None
        self._available = False

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}/ws"

    @property
    def available(self) -> bool:
        return self._available

    def async_add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a state change listener. Returns an unsubscribe function."""
        self._listeners.append(callback)

        def remove() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        return remove

    def _notify(self) -> None:
        for cb in self._listeners:
            cb()

    async def async_start(self) -> None:
        """Start the background WebSocket listener task."""
        self._task = self.hass.async_create_background_task(
            self._ws_loop(), "gaggimate_ws"
        )

    async def async_stop(self) -> None:
        """Stop the background listener task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _ws_loop(self) -> None:
        """Reconnecting WebSocket loop."""
        while True:
            try:
                await self._connect()
            except asyncio.CancelledError:
                return
            except Exception as err:
                _LOGGER.warning(
                    "GaggiMate: connection lost (%s), retrying in %ds",
                    err,
                    RECONNECT_DELAY,
                )

            if self._available:
                self._available = False
                self._notify()

            await asyncio.sleep(RECONNECT_DELAY)

    async def _connect(self) -> None:
        """Connect to WebSocket and process incoming events."""
        session = async_get_clientsession(self.hass)
        async with session.ws_connect(self.ws_url, heartbeat=30) as ws:
            _LOGGER.info("GaggiMate: connected to %s", self.ws_url)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        payload = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue
                    if payload.get("tp") == "evt:status":
                        self._available = True
                        self.data = payload
                        self._notify()
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

    async def async_set_mode(self, mode: int) -> None:
        """Send a mode change request to the device."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.ws_connect(self.ws_url) as ws:
                await ws.send_str(json.dumps({"tp": "req:change-mode", "mode": mode}))
        except Exception as err:
            _LOGGER.error("GaggiMate: failed to set mode: %s", err)
            raise
