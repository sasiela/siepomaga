"""The SiePomaga integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import SiePomagaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SiePomaga from a config entry."""
    coordinator = SiePomagaCoordinator(hass, entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # first refresh can fail (network, parse); coordinator will retry
        _LOGGER.warning(
            "SiePomaga (%s): pierwsze odświeżenie nie powiodło się: %s. Sensory będą dostępne po udanym odświeżeniu. W opcjach włącz „Zapisuj błędy do logów” po szczegóły.",
            entry.data.get("slug", entry.entry_id),
            err,
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok

