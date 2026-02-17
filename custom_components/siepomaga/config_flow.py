"""Config flow for SiePomaga integration."""

from __future__ import annotations

import re

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_FUNDRAISER,
    CONF_LOG_ERRORS,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    CONF_URL,
    DEFAULT_LOG_ERRORS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_URL_RE = re.compile(
    r"^https?://(www\.)?siepomaga\.pl/([a-z0-9-]+)/*$",
    re.IGNORECASE,
)
_SLUG_RE = re.compile(r"^[a-z0-9-]+$", re.IGNORECASE)


def _normalize_input(user_input: dict) -> tuple[str, str]:
    raw = (user_input.get(CONF_FUNDRAISER) or "").strip()
    m = _URL_RE.match(raw)
    if m:
        slug = m.group(2).lower()
        url = f"https://www.siepomaga.pl/{slug}"
        return slug, url

    if not _SLUG_RE.match(raw):
        raise ValueError("invalid")

    slug = raw.lower()
    url = f"https://www.siepomaga.pl/{slug}"
    return slug, url


class SiePomagaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SiePomaga."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                slug, url = _normalize_input(user_input)
            except ValueError:
                errors["base"] = "invalid_fundraiser"
            else:
                await self.async_set_unique_id(slug)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SiePomaga: {slug}",
                    data={CONF_SLUG: slug, CONF_URL: url},
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_LOG_ERRORS: DEFAULT_LOG_ERRORS,
                    },
                )

        schema = vol.Schema({vol.Required(CONF_FUNDRAISER): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return SiePomagaOptionsFlowHandler(config_entry)


class SiePomagaOptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handle options (OptionsFlowWithConfigEntry for wider HA version compatibility)."""

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options or {}
        current_interval = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        current_log_errors = bool(options.get(CONF_LOG_ERRORS, DEFAULT_LOG_ERRORS))
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.Coerce(int),
                vol.Optional(CONF_LOG_ERRORS, default=current_log_errors): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

