"""Support for Somat Smartwash binary sensors."""

from __future__ import annotations

from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SomatDataUpdateCoordinator
from .entity import SomatSmartwashEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Somat Smartwash binary sensor entities."""
    coordinator: SomatDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    devices = coordinator.data.get("devices", {})
    for device_id in devices:
        entities.extend(
            [
                SomatBatteryLowBinarySensor(coordinator, device_id),
                SomatRefillNeededBinarySensor(coordinator, device_id),
                SomatDishwasherRunningBinarySensor(coordinator, device_id),
                SomatConnectionBinarySensor(coordinator, device_id),
            ]
        )

    async_add_entities(entities)


class SomatBatteryLowBinarySensor(SomatSmartwashEntity, BinarySensorEntity):
    """Binary sensor indicating if the battery is low."""

    _attr_translation_key = "battery_low"
    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the battery binary sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_battery_low"

    @property
    def is_on(self) -> bool:
        """Return True if battery is low or warning."""
        battery = self.device_state.get("battery_level")
        return bool(battery and battery.lower() != "ok")


class SomatRefillNeededBinarySensor(SomatSmartwashEntity, BinarySensorEntity):
    """Binary sensor indicating if a cartridge refill is needed or problem detected."""

    _attr_translation_key = "refill_needed"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the refill problem sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_refill_needed"

    @property
    def is_on(self) -> bool:
        """Return True if refill is empty, missing, or fill level <= 10%."""
        refill_status = self.device_state.get("refill_status")
        if refill_status in ("empty", "missing", "error"):
            return True

        fill = self.device_state.get("detergent_fill_level")
        if fill is not None:
            try:
                return int(fill) <= 10
            except (ValueError, TypeError):
                pass
        return False


class SomatDishwasherRunningBinarySensor(SomatSmartwashEntity, BinarySensorEntity):
    """Binary sensor indicating if the dishwasher is actively in a wash cycle."""

    _attr_translation_key = "washing"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the running binary sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_washing"

    @property
    def is_on(self) -> bool:
        """Return True if dishwasher cycle is running."""
        status = self.device_state.get("wash_cycle_status")
        return bool(status and status.lower() not in ("idle", "ready", "done", "off"))


class SomatConnectionBinarySensor(SomatSmartwashEntity, BinarySensorEntity):
    """Binary sensor indicating if the device is currently connected to the cloud."""

    _attr_translation_key = "connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the connectivity binary sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_connected"

    @property
    def is_on(self) -> bool:
        """Return True if device is online with active cloud socket."""
        status = self.device_state.get("connection_status")
        return status == "connected"
