"""Config flow for GaggiMate integration."""

import asyncio
import json

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_HOST, DOMAIN


class GaggiMateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GaggiMate."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}

        if user_input is not None:
            host = user_input["host"].strip()
            try:
                await self._validate_host(host)
            except Exception:
                errors["host"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"GaggiMate ({host})",
                    data={"host": host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host", default=DEFAULT_HOST): str,
            }),
            errors=errors,
        )

    async def _validate_host(self, host: str) -> None:
        """Validate by connecting to the WebSocket and waiting for a status event."""
        url = f"ws://{host}/ws"
        session = async_get_clientsession(self.hass)
        async with asyncio.timeout(5):
            async with session.ws_connect(url) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                        except json.JSONDecodeError:
                            continue
                        if data.get("tp") == "evt:status":
                            return
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        raise ConnectionError("WebSocket closed unexpectedly")
        raise ConnectionError("No status event received")
