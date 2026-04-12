"""Switch platform for Aldockery."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DATA_ENTRY_NAME, DATA_ENTRIES, DATA_KNOWN_SWITCHES, DOMAIN


class AldockeryContainerSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, entry_id: str, entry_name: str, coordinator, container_name: str) -> None:
        super().__init__(coordinator)
        self.entry_id = entry_id
        self.entry_name = entry_name
        self.container_name = container_name

    @property
    def _item(self):
        return self.coordinator.data.get(self.container_name)

    @property
    def unique_id(self) -> str:
        return f"aldockery_beta_{self.entry_id}_{self.container_name}_switch"

    @property
    def name(self) -> str:
        return f"{self.entry_name} {self.container_name}"

    @property
    def is_on(self) -> bool:
        item = self._item
        return bool(item and item.get("state") == "running")

    @property
    def available(self) -> bool:
        return self.container_name in self.coordinator.data

    @property
    def extra_state_attributes(self):
        item = self._item
        if not item:
            return None
        return {
            "container": item["name"],
            "status": item["status"],
            "image": item["image"],
            "protected": item.get("protected", False),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.entry_id}_host")},
            name=f"{self.entry_name} Docker",
            manufacturer="Aldockery",
            model="Docker Host",
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(self.coordinator.api.start_container, self.container_name)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        item = self._item or {}
        if item.get("protected"):
            raise HomeAssistantError(f"Container is protected: {self.container_name}")
        await self.hass.async_add_executor_job(self.coordinator.api.stop_container, self.container_name)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    known = data[DATA_KNOWN_SWITCHES]
    entry_name = data[DATA_ENTRY_NAME]

    def add_missing_entities():
        new = []
        for key in sorted(coordinator.data.keys()):
            if key in known:
                continue
            known.add(key)
            new.append(AldockeryContainerSwitch(entry.entry_id, entry_name, coordinator, key))
        if new:
            async_add_entities(new)

    add_missing_entities()

    def _listener():
        add_missing_entities()

    entry.async_on_unload(coordinator.async_add_listener(_listener))
