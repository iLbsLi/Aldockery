"""Sensor platform for Aldockery."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DATA_ENTRY_NAME, DATA_ENTRIES, DATA_KNOWN_SENSORS, DOMAIN


class AldockeryContainerCountSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:docker"

    def __init__(self, entry_id: str, entry_name: str, coordinator) -> None:
        super().__init__(coordinator)
        self.entry_id = entry_id
        self.entry_name = entry_name

    @property
    def unique_id(self) -> str:
        return f"aldockery_beta_{self.entry_id}_container_count"

    @property
    def name(self) -> str:
        return f"{self.entry_name} container count"

    @property
    def native_value(self):
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        return {
            "last_successful_poll": self.coordinator.last_successful_poll,
            "last_error": self.coordinator.last_error,
            "containers": sorted(self.coordinator.data.keys()),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.entry_id}_host")},
            name=f"{self.entry_name} Docker",
            manufacturer="Aldockery",
            model="Docker Host",
        )

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    known = data[DATA_KNOWN_SENSORS]
    entry_name = data[DATA_ENTRY_NAME]

    if "container_count" not in known:
        known.add("container_count")
        async_add_entities([AldockeryContainerCountSensor(entry.entry_id, entry_name, coordinator)])
