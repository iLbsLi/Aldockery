"""Config flow for Aldockery."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import AldockeryAPI
from .const import (
    CONF_DOCKER_BIN,
    CONF_EXCLUDE_PATTERNS,
    CONF_INCLUDE_PATTERNS,
    CONF_MODE,
    CONF_NAME,
    CONF_PROTECTED_CONTAINERS,
    CONF_SCAN_INTERVAL,
    CONF_SSH_HOST,
    CONF_SSH_KEY,
    CONF_SSH_PORT,
    CONF_SSH_USER,
    DEFAULT_DOCKER_BIN,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSH_PORT,
    DOMAIN,
    MODE_LOCAL,
    MODE_SSH,
)


def _csv_to_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _base_schema(defaults=None):
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_MODE, default=defaults.get(CONF_MODE, MODE_SSH)): vol.In([MODE_LOCAL, MODE_SSH]),
            vol.Required(CONF_DOCKER_BIN, default=defaults.get(CONF_DOCKER_BIN, DEFAULT_DOCKER_BIN)): str,
            vol.Required(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
            vol.Optional(CONF_SSH_USER, default=defaults.get(CONF_SSH_USER, "")): str,
            vol.Optional(CONF_SSH_HOST, default=defaults.get(CONF_SSH_HOST, "")): str,
            vol.Optional(CONF_SSH_KEY, default=defaults.get(CONF_SSH_KEY, "")): str,
            vol.Optional(CONF_SSH_PORT, default=defaults.get(CONF_SSH_PORT, DEFAULT_SSH_PORT)): int,
            vol.Optional(CONF_INCLUDE_PATTERNS, default=defaults.get(CONF_INCLUDE_PATTERNS, "")): str,
            vol.Optional(CONF_EXCLUDE_PATTERNS, default=defaults.get(CONF_EXCLUDE_PATTERNS, "")): str,
            vol.Optional(CONF_PROTECTED_CONTAINERS, default=defaults.get(CONF_PROTECTED_CONTAINERS, "")): str,
        }
    )


class AldockeryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            mode = user_input[CONF_MODE]
            if mode == MODE_SSH:
                for field in (CONF_SSH_USER, CONF_SSH_HOST, CONF_SSH_KEY):
                    if not user_input.get(field):
                        errors["base"] = "missing_ssh_fields"
                        break

            if not errors:
                try:
                    await self.hass.async_add_executor_job(AldockeryAPI(dict(user_input)).test_connection)
                except Exception:
                    errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(self._build_unique(user_input))
                self._abort_if_unique_id_configured()
                data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_MODE: user_input[CONF_MODE],
                    CONF_DOCKER_BIN: user_input[CONF_DOCKER_BIN],
                    CONF_SSH_USER: user_input.get(CONF_SSH_USER, ""),
                    CONF_SSH_HOST: user_input.get(CONF_SSH_HOST, ""),
                    CONF_SSH_KEY: user_input.get(CONF_SSH_KEY, ""),
                    CONF_SSH_PORT: user_input.get(CONF_SSH_PORT, DEFAULT_SSH_PORT),
                }
                options = {
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_INCLUDE_PATTERNS: _csv_to_list(user_input.get(CONF_INCLUDE_PATTERNS, "")),
                    CONF_EXCLUDE_PATTERNS: _csv_to_list(user_input.get(CONF_EXCLUDE_PATTERNS, "")),
                    CONF_PROTECTED_CONTAINERS: _csv_to_list(user_input.get(CONF_PROTECTED_CONTAINERS, "")),
                }
                return self.async_create_entry(title=user_input[CONF_NAME], data=data, options=options)

        return self.async_show_form(step_id="user", data_schema=_base_schema(user_input), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return AldockeryOptionsFlow()

    def _build_unique(self, data):
        if data[CONF_MODE] == MODE_LOCAL:
            return f"local:{data.get(CONF_NAME, DEFAULT_NAME)}:{data.get(CONF_DOCKER_BIN, DEFAULT_DOCKER_BIN)}"
        return f"ssh:{data.get(CONF_SSH_USER,'')}@{data.get(CONF_SSH_HOST,'')}:{data.get(CONF_SSH_PORT, DEFAULT_SSH_PORT)}"


class AldockeryOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}
        current = dict(self.config_entry.data)
        current.update({
            CONF_SCAN_INTERVAL: self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            CONF_INCLUDE_PATTERNS: ", ".join(self.config_entry.options.get(CONF_INCLUDE_PATTERNS, [])),
            CONF_EXCLUDE_PATTERNS: ", ".join(self.config_entry.options.get(CONF_EXCLUDE_PATTERNS, [])),
            CONF_PROTECTED_CONTAINERS: ", ".join(self.config_entry.options.get(CONF_PROTECTED_CONTAINERS, [])),
        })

        if user_input is not None:
            mode = user_input[CONF_MODE]
            if mode == MODE_SSH:
                for field in (CONF_SSH_USER, CONF_SSH_HOST, CONF_SSH_KEY):
                    if not user_input.get(field):
                        errors["base"] = "missing_ssh_fields"
                        break

            if not errors:
                try:
                    await self.hass.async_add_executor_job(AldockeryAPI(dict(user_input)).test_connection)
                except Exception:
                    errors["base"] = "cannot_connect"

            if not errors:
                data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_MODE: user_input[CONF_MODE],
                    CONF_DOCKER_BIN: user_input[CONF_DOCKER_BIN],
                    CONF_SSH_USER: user_input.get(CONF_SSH_USER, ""),
                    CONF_SSH_HOST: user_input.get(CONF_SSH_HOST, ""),
                    CONF_SSH_KEY: user_input.get(CONF_SSH_KEY, ""),
                    CONF_SSH_PORT: user_input.get(CONF_SSH_PORT, DEFAULT_SSH_PORT),
                }
                options = {
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_INCLUDE_PATTERNS: _csv_to_list(user_input.get(CONF_INCLUDE_PATTERNS, "")),
                    CONF_EXCLUDE_PATTERNS: _csv_to_list(user_input.get(CONF_EXCLUDE_PATTERNS, "")),
                    CONF_PROTECTED_CONTAINERS: _csv_to_list(user_input.get(CONF_PROTECTED_CONTAINERS, "")),
                }
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=user_input[CONF_NAME],
                    data=data,
                    options=options,
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=_base_schema(current), errors=errors)
