"""DataUpdateCoordinator for Somat Smartwash."""

from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import SomatApiError, SomatAuthError, SomatSmartwashApiClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SomatDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Somat Smartwash data from the cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SomatSmartwashApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Somat Smartwash API."""
        try:
            device_list = await self.client.async_get_devices()
            devices_data: Dict[str, Any] = {}

            for dev in device_list:
                dev_id = dev["id"]
                device_details = await self.client.async_get_device(dev_id)
                devices_data[dev_id] = device_details

            # Fetch activity stats
            activity_data = await self.client.async_get_activity()

            return {
                "devices": devices_data,
                "activity": activity_data,
            }

        except SomatAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed: {err}"
            ) from err
        except SomatApiError as err:
            raise UpdateFailed(f"Error communicating with Somat API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
