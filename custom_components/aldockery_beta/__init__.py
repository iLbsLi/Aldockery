"""Aldockery config-entry integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .api import AldockeryAPI
from .coordinator import AldockeryCoordinator
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_INCLUDE_PATTERNS,
    CONF_EXCLUDE_PATTERNS,
    CONF_PROTECTED_CONTAINERS,
    DATA_API,
    DATA_COORDINATOR,
    DATA_ENTRIES,
    DATA_ENTRY_NAME,
    DATA_KNOWN_SWITCHES,
    DATA_KNOWN_BUTTONS,
    DATA_KNOWN_SENSORS,
    DATA_KNOWN_BINARY_SENSORS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_START_CONTAINER,
    SERVICE_STOP_CONTAINER,
    SERVICE_RESTART_CONTAINER,
    SERVICE_REDISCOVER,
    SERVICE_PRUNE_MISSING,
    SERVICE_TEST_CONNECTION,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        vol.Optional("host"): str,
        vol.Optional("container"): str,
    }
)

async def async_setup(hass: HomeAssistant, config) -> bool:
    hass.data.setdefault(DOMAIN, {DATA_ENTRIES: {}, "services_registered": False})
    if not hass.data[DOMAIN]["services_registered"]:
        _register_services(hass)
        hass.data[DOMAIN]["services_registered"] = True
    return True

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    include_patterns = entry.options.get(CONF_INCLUDE_PATTERNS, [])
    exclude_patterns = entry.options.get(CONF_EXCLUDE_PATTERNS, [])
    protected_containers = entry.options.get(CONF_PROTECTED_CONTAINERS, [])
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    api = AldockeryAPI(dict(entry.data))
    coordinator = AldockeryCoordinator(
        hass,
        api=api,
        scan_interval=scan_interval,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        protected_containers=protected_containers,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][DATA_ENTRIES][entry.entry_id] = {
        DATA_API: api,
        DATA_COORDINATOR: coordinator,
        DATA_ENTRY_NAME: entry.title,
        DATA_KNOWN_SWITCHES: set(),
        DATA_KNOWN_BUTTONS: set(),
        DATA_KNOWN_SENSORS: set(),
        DATA_KNOWN_BINARY_SENSORS: set(),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    _LOGGER.info("Aldockery entry %s loaded with %s containers", entry.title, len(coordinator.data))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN][DATA_ENTRIES].pop(entry.entry_id, None)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

def _resolve_entries(hass: HomeAssistant, call: ServiceCall):
    entries = hass.data[DOMAIN][DATA_ENTRIES]
    entry_id = call.data.get("entry_id")
    host = call.data.get("host")

    if entry_id:
        item = entries.get(entry_id)
        if not item:
            raise HomeAssistantError(f"Unknown entry_id: {entry_id}")
        return [(entry_id, item)]

    if host:
        matches = [(eid, item) for eid, item in entries.items() if item[DATA_ENTRY_NAME] == host]
        if not matches:
            raise HomeAssistantError(f"Unknown host: {host}")
        return matches

    return list(entries.items())

async def _service_container_action(hass: HomeAssistant, call: ServiceCall, action: str):
    container = call.data.get("container")
    if not container:
        raise HomeAssistantError("container is required")
    matches = _resolve_entries(hass, call)
    if len(matches) != 1:
        raise HomeAssistantError("Specify entry_id or host so exactly one entry is targeted")

    _, item = matches[0]
    api = item[DATA_API]
    coordinator = item[DATA_COORDINATOR]

    if action == SERVICE_STOP_CONTAINER and container in coordinator.protected_containers:
        raise HomeAssistantError(f"Container is protected: {container}")

    if action == SERVICE_START_CONTAINER:
        await hass.async_add_executor_job(api.start_container, container)
    elif action == SERVICE_STOP_CONTAINER:
        await hass.async_add_executor_job(api.stop_container, container)
    elif action == SERVICE_RESTART_CONTAINER:
        await hass.async_add_executor_job(api.restart_container, container)

    await coordinator.async_request_refresh()

async def _service_test_connection(hass: HomeAssistant, call: ServiceCall):
    matches = _resolve_entries(hass, call)
    if len(matches) != 1:
        raise HomeAssistantError("Specify entry_id or host so exactly one entry is targeted")
    _, item = matches[0]
    await hass.async_add_executor_job(item[DATA_API].test_connection)

async def _service_rediscover(hass: HomeAssistant, call: ServiceCall):
    for _, item in _resolve_entries(hass, call):
        await item[DATA_COORDINATOR].async_request_refresh()

async def _service_prune_missing(hass: HomeAssistant, call: ServiceCall):
    registry = er.async_get(hass)

    for entry_id, item in _resolve_entries(hass, call):
        coordinator = item[DATA_COORDINATOR]
        current = set(coordinator.data.keys())
        prefix = f"aldockery_beta_{entry_id}_"

        to_remove = []
        for entity in list(registry.entities.values()):
            if entity.platform != DOMAIN:
                continue
            if entity.config_entry_id != entry_id:
                continue
            if not entity.unique_id.startswith(prefix):
                continue

            suffixes = ["_switch", "_start", "_stop", "_restart"]
            container_name = None
            for suffix in suffixes:
                if entity.unique_id.endswith(suffix):
                    container_name = entity.unique_id[len(prefix):-len(suffix)]
                    break
            if container_name is None:
                continue

            if container_name not in current:
                to_remove.append(entity.entity_id)

        for entity_id in to_remove:
            registry.async_remove(entity_id)

def _register_services(hass: HomeAssistant) -> None:
    async def _start(call: ServiceCall) -> None:
        await _service_container_action(hass, call, SERVICE_START_CONTAINER)

    async def _stop(call: ServiceCall) -> None:
        await _service_container_action(hass, call, SERVICE_STOP_CONTAINER)

    async def _restart(call: ServiceCall) -> None:
        await _service_container_action(hass, call, SERVICE_RESTART_CONTAINER)

    async def _rediscover(call: ServiceCall) -> None:
        await _service_rediscover(hass, call)

    async def _prune(call: ServiceCall) -> None:
        await _service_prune_missing(hass, call)

    async def _test(call: ServiceCall) -> None:
        await _service_test_connection(hass, call)

    hass.services.async_register(DOMAIN, SERVICE_START_CONTAINER, _start, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP_CONTAINER, _stop, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RESTART_CONTAINER, _restart, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REDISCOVER, _rediscover, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_PRUNE_MISSING, _prune, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TEST_CONNECTION, _test, schema=SERVICE_SCHEMA)
