"""Config and options flow for Netztest AT."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import parse_times
from .binary import BinaryError, async_ensure_binary
from .const import (
    CONF_ACCEPT_TERMS,
    CONF_PLAN_DOWNLOAD,
    CONF_PLAN_UPLOAD,
    CONF_SCHEDULE_ENABLED,
    CONF_RANDOM_DELAY,
    CONF_START_TIMES,
    DEFAULT_RANDOM_DELAY,
    DEFAULT_SCHEDULE_ENABLED,
    DOMAIN,
    MAX_RANDOM_DELAY,
    TERMS_URL,
)

_RATE = selector.NumberSelector(
    selector.NumberSelectorConfig(min=1, max=100000, step=0.1, unit_of_measurement="Mbit/s", mode=selector.NumberSelectorMode.BOX)
)


def _schema(values: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SCHEDULE_ENABLED, default=values.get(CONF_SCHEDULE_ENABLED, DEFAULT_SCHEDULE_ENABLED)): bool,
            vol.Required(CONF_START_TIMES, default=values.get(CONF_START_TIMES) or ""): str,
            vol.Required(CONF_RANDOM_DELAY, default=values.get(CONF_RANDOM_DELAY, DEFAULT_RANDOM_DELAY)): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=MAX_RANDOM_DELAY, step=1, unit_of_measurement="min", mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(CONF_PLAN_DOWNLOAD, description={"suggested_value": values.get(CONF_PLAN_DOWNLOAD)}): _RATE,
            vol.Optional(CONF_PLAN_UPLOAD, description={"suggested_value": values.get(CONF_PLAN_UPLOAD)}): _RATE,
        }
    )


def _validate(user_input: dict[str, Any] | None) -> dict[str, str]:
    if user_input is None:
        return {}
    errors: dict[str, str] = {}
    if user_input.get(CONF_SCHEDULE_ENABLED, True) or user_input.get(CONF_START_TIMES, "").strip():
        try:
            parse_times(user_input.get(CONF_START_TIMES, ""))
        except ValueError:
            errors[CONF_START_TIMES] = "invalid_times"
    if not user_input.get(CONF_ACCEPT_TERMS):
        errors["base"] = "terms_required"
    return errors


def _with_terms(schema: vol.Schema, values: dict[str, Any]) -> vol.Schema:
    return schema.extend({vol.Required(CONF_ACCEPT_TERMS, default=bool(values.get(CONF_ACCEPT_TERMS, False))): bool})


class RtrConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-instance setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        try:
            await async_ensure_binary(self.hass)
        except BinaryError as err:
            return self.async_abort(reason="binary_unavailable", description_placeholders={"error": str(err)})
        errors = _validate(user_input)
        if user_input is not None and not errors:
            return self.async_create_entry(title="Netztest AT", data=user_input)
        schema = _with_terms(_schema(user_input or {}), user_input or {})
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors, description_placeholders={"terms_url": TERMS_URL}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RtrOptionsFlow()


class RtrOptionsFlow(OptionsFlow):
    """Change schedule and contract values."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = _validate(user_input)
        if user_input is not None and not errors:
            # Store cleared optional fields explicitly, otherwise the value from the initial setup would apply again.
            return self.async_create_entry(
                data={CONF_PLAN_DOWNLOAD: None, CONF_PLAN_UPLOAD: None, **user_input}
            )
        current = user_input or {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_with_terms(_schema(current), current),
            errors=errors,
            description_placeholders={"terms_url": TERMS_URL},
        )
