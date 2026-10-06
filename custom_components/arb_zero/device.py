"""Bluetooth connection to an ARB Zero fridge."""

from __future__ import annotations

import asyncio
import logging

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import REPLY_TIMEOUT
from .protocol import (
    NOTIFY_UUID,
    WRITE_UUID,
    ArbZeroStatus,
    Setting,
    build_command,
    build_status_request,
    parse_status,
)

_LOGGER = logging.getLogger(__name__)


class ArbZeroError(Exception):
    """Raised when the fridge can't be reached or doesn't answer."""


class ArbZeroDevice:
    """Keeps a connection open and talks to the fridge."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self._hass = hass
        self.address = address
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._reply: asyncio.Future[ArbZeroStatus] | None = None

    def _ble_device(self):
        return bluetooth.async_ble_device_from_address(
            self._hass, self.address, connectable=True
        )

    async def _ensure_connected(self) -> BleakClientWithServiceCache:
        if self._client is not None and self._client.is_connected:
            return self._client
        ble_device = self._ble_device()
        if ble_device is None:
            raise ArbZeroError(
                f"ARB Zero {self.address} not found by any connectable Bluetooth "
                "adapter or proxy"
            )
        _LOGGER.debug("Connecting to %s", self.address)
        client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            f"ARB Zero {self.address}",
            disconnected_callback=self._on_disconnect,
            ble_device_callback=lambda: self._ble_device() or ble_device,
        )
        try:
            await client.start_notify(NOTIFY_UUID, self._on_notify)
        except Exception:
            await client.disconnect()
            raise
        self._client = client
        return client

    def _on_disconnect(self, _client) -> None:
        _LOGGER.debug("Disconnected from %s", self.address)
        self._client = None

    def _on_notify(self, _char: BleakGATTCharacteristic, data: bytearray) -> None:
        status = parse_status(data)
        if status is None:
            _LOGGER.debug("Ignoring packet from %s: %s", self.address, data.hex(" "))
            return
        if self._reply is not None and not self._reply.done():
            self._reply.set_result(status)

    async def _write(self, packet: bytes) -> None:
        client = await self._ensure_connected()
        await client.write_gatt_char(WRITE_UUID, packet, response=False)

    async def async_get_status(self) -> ArbZeroStatus:
        """Ask the fridge for its status and wait for the reply."""
        async with self._lock:
            try:
                self._reply = asyncio.get_running_loop().create_future()
                await self._write(build_status_request())
                return await asyncio.wait_for(self._reply, REPLY_TIMEOUT)
            except TimeoutError as err:
                await self._disconnect()
                raise ArbZeroError("No status reply from the fridge") from err
            except ArbZeroError:
                raise
            except Exception as err:  # bleak raises many different errors
                await self._disconnect()
                raise ArbZeroError(f"Bluetooth error: {err}") from err
            finally:
                self._reply = None

    async def async_set(self, setting: Setting, value: int) -> None:
        """Change one setting on the fridge."""
        async with self._lock:
            try:
                await self._write(build_command(setting, value))
            except ArbZeroError:
                raise
            except Exception as err:
                await self._disconnect()
                raise ArbZeroError(f"Bluetooth error: {err}") from err

    async def _disconnect(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Error while disconnecting", exc_info=True)

    async def async_disconnect(self) -> None:
        """Close the connection."""
        async with self._lock:
            await self._disconnect()
