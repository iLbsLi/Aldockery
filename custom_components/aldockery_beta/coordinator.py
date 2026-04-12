"""Coordinator for Aldockery."""
from __future__ import annotations

import fnmatch
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AldockeryAPI
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AldockeryCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Poll Docker and handle filters."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: AldockeryAPI,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        protected_containers: list[str] | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.protected_containers = protected_containers or []
        self.last_successful_poll: str | None = None
        self.last_error: str | None = None

    def _included(self, name: str) -> bool:
        if self.include_patterns and not any(fnmatch.fnmatch(name, p) for p in self.include_patterns):
            return False
        if self.exclude_patterns and any(fnmatch.fnmatch(name, p) for p in self.exclude_patterns):
            return False
        return True

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            data = await self.hass.async_add_executor_job(self.api.list_containers)
        except Exception as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err

        filtered = {}
        for name, item in data.items():
            if not self._included(name):
                continue
            item = dict(item)
            item["protected"] = name in self.protected_containers
            filtered[name] = item

        self.last_successful_poll = datetime.utcnow().isoformat() + "Z"
        self.last_error = None
        return filtered
