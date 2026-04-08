"""GaggiMate WebSocket coordinator."""

import asyncio
import json
import logging
import uuid
from typing import Any, Callable

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

RECONNECT_DELAY = 5  # seconds
REQUEST_TIMEOUT = 30  # seconds


class GaggiMateCoordinator:
    """Maintains a persistent WebSocket connection and pushes status updates to listeners."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self.hass = hass
        self.host = host
        self.data: dict[str, Any] = {}
        self.profiles: list[dict[str, Any]] = []
        self._listeners: list[Callable[[], None]] = []
        self._task: asyncio.Task | None = None
        self._available = False
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._pending_requests: dict[str, asyncio.Future] = {}

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
            self._ws = ws
            _LOGGER.info("GaggiMate: connected to %s", self.ws_url)

            # Fetch profiles on connect
            try:
                await self.async_refresh_profiles()
            except Exception as err:
                _LOGGER.warning("GaggiMate: failed to load profiles: %s", err)

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        payload = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    # Route responses to pending requests
                    rid = payload.get("rid")
                    if rid and rid in self._pending_requests:
                        self._pending_requests[rid].set_result(payload)
                        continue

                    if payload.get("tp") == "evt:status":
                        self._available = True
                        self.data = payload
                        self._notify()
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
            self._ws = None

    async def async_request(self, data: dict) -> dict:
        """Send a request on the persistent WS and wait for a matching response."""
        if not self._ws or self._ws.closed:
            raise ConnectionError("Not connected to GaggiMate")

        rid = str(uuid.uuid4())
        data["rid"] = rid
        future: asyncio.Future = self.hass.loop.create_future()
        self._pending_requests[rid] = future

        try:
            await self._ws.send_str(json.dumps(data))
            return await asyncio.wait_for(future, timeout=REQUEST_TIMEOUT)
        finally:
            self._pending_requests.pop(rid, None)

    async def async_refresh_profiles(self) -> None:
        """Fetch the profile list from the device."""
        response = await self.async_request({"tp": "req:profiles:list"})
        self.profiles = response.get("profiles", [])
        self._notify()

    async def async_select_profile(self, profile_id: str) -> None:
        """Select a profile by ID."""
        await self.async_request({"tp": "req:profiles:select", "id": profile_id})
        await self.async_refresh_profiles()

    async def async_set_mode(self, mode: int) -> None:
        """Send a mode change request to the device."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.ws_connect(self.ws_url) as ws:
                await ws.send_str(json.dumps({"tp": "req:change-mode", "mode": mode}))
        except Exception as err:
            _LOGGER.error("GaggiMate: failed to set mode: %s", err)
            raise

    async def async_flush(self) -> None:
        """Send a flush request to the device."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.ws_connect(self.ws_url) as ws:
                await ws.send_str(json.dumps({"tp": "req:flush:start"}))
        except Exception as err:
            _LOGGER.error("GaggiMate: failed to start flush: %s", err)
            raise
