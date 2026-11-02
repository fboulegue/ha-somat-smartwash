"""Support for Somat Smartwash sensors."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
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
    """Set up Somat Smartwash sensor entities."""
    coordinator: SomatDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    devices = coordinator.data.get("devices", {})
    for device_id in devices:
        entities.extend(
            [
                SomatDetergentFillSensor(coordinator, device_id),
                SomatWashCycleStatusSensor(coordinator, device_id),
                SomatProgramSensor(coordinator, device_id),
                SomatRefillStatusSensor(coordinator, device_id),
                SomatWaterHardnessSensor(coordinator, device_id),
                SomatWifiRssiSensor(coordinator, device_id),
                SomatWashCycleCountSensor(coordinator, device_id),
                SomatRefillCountSensor(coordinator, device_id),
            ]
        )

    async_add_entities(entities)


class SomatDetergentFillSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for detergent fill level percentage."""

    _attr_translation_key = "detergent_fill_level"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cup-water"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the fill level sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_detergent_fill_level"

    @property
    def native_value(self) -> Optional[int]:
        """Return the detergent fill percentage."""
        val = self.device_state.get("detergent_fill_level")
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        fill = self.native_value
        estimated_doses = round(fill * 0.3) if fill is not None else None
        return {
            "refill_status": self.device_state.get("refill_status"),
            "estimated_doses_remaining": estimated_doses,
        }


class SomatWashCycleStatusSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for current wash cycle status."""

    _attr_translation_key = "wash_cycle_status"
    _attr_icon = "mdi:dishwasher"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the wash cycle status sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_wash_cycle_status"

    @property
    def native_value(self) -> Optional[str]:
        """Return the wash cycle status."""
        return self.device_state.get("wash_cycle_status")


class SomatProgramSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for current dosing program."""

    _attr_translation_key = "program"
    _attr_icon = "mdi:tune-vertical"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the program sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_program"

    @property
    def native_value(self) -> Optional[str]:
        """Return the active program."""
        return self.device_state.get("program")


class SomatRefillStatusSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for refill cartridge physical status."""

    _attr_translation_key = "refill_status"
    _attr_icon = "mdi:package-variant-closed"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the refill status sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_refill_status"

    @property
    def native_value(self) -> Optional[str]:
        """Return the refill status."""
        return self.device_state.get("refill_status")


class SomatWaterHardnessSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for water hardness setting."""

    _attr_translation_key = "water_hardness"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:water-opacity"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the water hardness sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_water_hardness"

    @property
    def native_value(self) -> Optional[str]:
        """Return the water hardness level."""
        return self.device_state.get("water_hardness")


class SomatWifiRssiSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for Wi-Fi signal strength."""

    _attr_translation_key = "wifi_rssi"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the Wi-Fi RSSI sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_wifi_rssi"

    @property
    def native_value(self) -> Optional[int]:
        """Return Wi-Fi RSSI."""
        rssi = self.device_state.get("wifi_rssi")
        if rssi is not None:
            try:
                return int(rssi)
            except (ValueError, TypeError):
                return None
        return None


class SomatWashCycleCountSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for total wash cycle count."""

    _attr_translation_key = "wash_cycle_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the cycle count sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_wash_cycle_count"

    @property
    def native_value(self) -> int:
        """Return total wash cycles completed."""
        activity = self.coordinator.data.get("activity", {})
        return int(activity.get("washCycleCount", 0))


class SomatRefillCountSensor(SomatSmartwashEntity, SensorEntity):
    """Sensor for total refill changes count."""

    _attr_translation_key = "refill_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:package-variant"

    def __init__(
        self,
        coordinator: SomatDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the refill count sensor."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_refill_count"

    @property
    def native_value(self) -> int:
        """Return total refills consumed."""
        activity = self.coordinator.data.get("activity", {})
        return int(activity.get("refillCount", 0))
