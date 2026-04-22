"""Button platform for Aldockery."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DATA_ENTRY_NAME, DATA_ENTRIES, DATA_KNOWN_BUTTONS, DOMAIN
from .naming import button_suggested_object_id, button_unique_id


class _BaseContainerButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    action_name = ""

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
        return button_unique_id(self.entry_id, self.entry_name, self.container_name, self.action_name)

    @property
    def name(self) -> str:
        return f"{self.container_name} {self.action_name}"

    @property
    def suggested_object_id(self) -> str:
        return button_suggested_object_id(self.entry_name, self.container_name, self.action_name)

    @property
    def available(self) -> bool:
        return self.container_name in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.entry_id}_host")},
            name=f"{self.entry_name} Docker",
            manufacturer="Aldockery",
            model="Docker Host",
        )

class AldockeryStartButton(_BaseContainerButton):
    action_name = "start"
    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.api.start_container, self.container_name)
        await self.coordinator.async_request_refresh()

class AldockeryStopButton(_BaseContainerButton):
    action_name = "stop"
    @property
    def available(self) -> bool:
        item = self._item
        return bool(item) and not item.get("protected", False)
    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.api.stop_container, self.container_name)
        await self.coordinator.async_request_refresh()

class AldockeryRestartButton(_BaseContainerButton):
    action_name = "restart"
    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self.coordinator.api.restart_container, self.container_name)
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    known = data[DATA_KNOWN_BUTTONS]
    entry_name = data[DATA_ENTRY_NAME]

    def add_missing_entities():
        new = []
        for key in sorted(coordinator.data.keys()):
            if key in known:
                continue
            known.add(key)
            new.extend([
                AldockeryStartButton(entry.entry_id, entry_name, coordinator, key),
                AldockeryStopButton(entry.entry_id, entry_name, coordinator, key),
                AldockeryRestartButton(entry.entry_id, entry_name, coordinator, key),
            ])
        if new:
            async_add_entities(new)

    add_missing_entities()

    def _listener():
        add_missing_entities()

    entry.async_on_unload(coordinator.async_add_listener(_listener))
