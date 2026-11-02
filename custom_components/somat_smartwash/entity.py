"""Base entity for Somat Smartwash."""

from __future__ import annotations

from typing import Any, Dict

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SomatDataUpdateCoordinator


class SomatSmartwashEntity(CoordinatorEntity[SomatDataUpdateCoordinator]):
    """Defines a base Somat Smartwash entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device_id = device_id
        dev_name = self.device_state.get("name") or "Somat smartwash"
        setup_status = self.device_state.get("setup_status")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=dev_name,
            manufacturer="Henkel / Somat",
            model="Somat Smartwash",
            sw_version=setup_status if setup_status else None,
            configuration_url="https://www.somat-smartwash.com",
        )

    @property
    def device_data(self) -> Dict[str, Any]:
        """Return the device data dictionary from coordinator."""
        if self.coordinator.data and "devices" in self.coordinator.data:
            return self.coordinator.data["devices"].get(self.device_id, {})
        return {}

    @property
    def device_state(self) -> Dict[str, Any]:
        """Return properties dictionary of the device."""
        return self.device_data.get("state", {})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and bool(self.device_data)
        )
