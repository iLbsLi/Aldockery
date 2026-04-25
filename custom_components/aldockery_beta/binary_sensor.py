"""Binary sensor platform for Aldockery."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DATA_ENTRY_NAME, DATA_ENTRIES, DATA_KNOWN_BINARY_SENSORS, DOMAIN
from .naming import sensor_suggested_object_id


class AldockeryHostReachableBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:lan-connect"

    def __init__(self, entry_id: str, entry_name: str, coordinator) -> None:
        super().__init__(coordinator)
        self.entry_id = entry_id
        self.entry_name = entry_name

    @property
    def unique_id(self) -> str:
        return f"aldockery_beta_{self.entry_id}_host_reachable"

    @property
    def name(self) -> str:
        return "reachable Docker"

    @property
    def suggested_object_id(self) -> str:
        return sensor_suggested_object_id("reachable")

    @property
    def is_on(self):
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        return {
            "last_successful_poll": self.coordinator.last_successful_poll,
            "last_error": self.coordinator.last_error,
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.entry_id}_host")},
            name=self.entry_name,
            manufacturer="Aldockery",
            model="Docker Host",
        )

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    known = data[DATA_KNOWN_BINARY_SENSORS]
    entry_name = data[DATA_ENTRY_NAME]

    if "reachable" not in known:
        known.add("reachable")
        async_add_entities([AldockeryHostReachableBinarySensor(entry.entry_id, entry_name, coordinator)])
