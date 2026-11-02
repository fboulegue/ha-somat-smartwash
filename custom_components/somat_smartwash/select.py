"""Support for Somat Smartwash select entities."""

from __future__ import annotations

import logging
from typing import Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import AVAILABLE_PROGRAMS, DOMAIN
from .coordinator import SomatDataUpdateCoordinator
from .entity import SomatSmartwashEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Somat Smartwash select entities."""
    coordinator: SomatDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = []

    devices = coordinator.data.get("devices", {})
    for device_id in devices:
        entities.append(SomatProgramSelectEntity(coordinator, device_id))

    async_add_entities(entities)


class SomatProgramSelectEntity(SomatSmartwashEntity, SelectEntity):
    """Select entity for changing the dosing program."""

    _attr_translation_key = "program_select"
    _attr_options = AVAILABLE_PROGRAMS
    _attr_icon = "mdi:tune-vertical"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the program select entity."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_select_program"

    @property
    def current_option(self) -> Optional[str]:
        """Return the current selected program."""
        prog = self.device_state.get("program")
        if prog in self._attr_options:
            return prog
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected program."""
        _LOGGER.debug(
            "Setting program to %s for device %s", option, self.device_id
        )
        await self.coordinator.client.async_update_device_property(
            self.device_id, "program", option
        )

        # Optimistically update coordinator state
        if (
            self.coordinator.data
            and "devices" in self.coordinator.data
            and self.device_id in self.coordinator.data["devices"]
        ):
            self.coordinator.data["devices"][self.device_id].setdefault(
                "state", {}
            )["program"] = option
            self.async_write_ha_state()

        # Trigger refresh to confirm cloud sync
        await self.coordinator.async_request_refresh()
