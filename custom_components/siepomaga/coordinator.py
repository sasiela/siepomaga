"""Data update coordinator for SiePomaga integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_PERMALINKS_URL,
    CONF_LOG_ERRORS,
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    CONF_URL,
    DEFAULT_LOG_ERRORS,
    DEFAULT_SCAN_INTERVAL,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FundraiserData:
    """Parsed fundraiser data from API."""

    raised_pln: int | None
    missing_pln: int | None
    goal_pln: int | None
    percent: float | None
    supporters: int | None
    steady_supporters: int | None
    start_date: date | None
    end_date: date | None
    title: str | None
    url: str
    slug: str


def _parse_api_response(data: object, url: str, slug: str) -> FundraiserData | None:
    """Parsuj odpowiedź API siepomaga.pl: /api/donor/web/v2/permalinks/{slug}?locale=pl."""
    if not isinstance(data, dict):
        return None
    target = data.get("data", {}).get("target") if isinstance(data.get("data"), dict) else None
    if not isinstance(target, dict):
        return None
    needy = target.get("needy")
    if not isinstance(needy, dict):
        return None
    cause = needy.get("cause")
    if not isinstance(cause, dict):
        return None
    funds_current = cause.get("funds_current")
    funds_aim = cause.get("funds_aim")
    if funds_current is None and funds_aim is None:
        return None
    try:
        raised = int(funds_current) if funds_current is not None else None
    except (TypeError, ValueError):
        raised = None
    try:
        goal = int(funds_aim) if funds_aim is not None else None
    except (TypeError, ValueError):
        goal = None
    if raised is None and goal is None:
        return None
    percent = None
    if goal and goal > 0 and raised is not None:
        percent = round(100.0 * raised / goal, 2)
    missing = (goal - raised) if (goal is not None and raised is not None) else None
    donors_count = cause.get("donors_count")
    try:
        supporters = int(donors_count) if donors_count is not None else None
    except (TypeError, ValueError):
        supporters = None
    constant = needy.get("constant_helps_count")
    try:
        steady_supporters = int(constant) if constant is not None else None
    except (TypeError, ValueError):
        steady_supporters = None
    start_date = None
    accepted = cause.get("accepted_at")
    if isinstance(accepted, str) and len(accepted) >= 10:
        try:
            start_date = datetime.fromisoformat(accepted.replace("Z", "+00:00")[:19]).date()
        except (ValueError, TypeError):
            pass
    end_date = None
    end_str = cause.get("end_date")
    if isinstance(end_str, str) and len(end_str) >= 10:
        try:
            end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00")[:19]).date()
        except (ValueError, TypeError):
            pass
    title = cause.get("title") if isinstance(cause.get("title"), str) else None
    return FundraiserData(
        raised_pln=raised,
        missing_pln=missing,
        goal_pln=goal,
        percent=percent,
        supporters=supporters,
        steady_supporters=steady_supporters,
        start_date=start_date,
        end_date=end_date,
        title=title,
        url=url,
        slug=slug,
    )


class SiePomagaCoordinator(DataUpdateCoordinator[FundraiserData]):
    """Fetch fundraiser data from siepomaga.pl API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.slug: str = entry.data[CONF_SLUG]
        self.url: str = entry.data[CONF_URL]
        options = entry.options or {}
        scan_interval = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        self._log_errors_default = bool(options.get(CONF_LOG_ERRORS, DEFAULT_LOG_ERRORS))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"SiePomaga {self.slug}",
            update_interval=timedelta(seconds=scan_interval),
        )

    def _log_errors(self) -> bool:
        opts = self.entry.options or {}
        return bool(opts.get(CONF_LOG_ERRORS, self._log_errors_default))

    async def _async_update_data(self) -> FundraiserData:
        session = async_get_clientsession(self.hass)
        log_errors = self._log_errors()
        api_url = f"{API_PERMALINKS_URL}/{self.slug}?locale=pl"

        try:
            resp = await asyncio.wait_for(
                session.get(
                    api_url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "application/json",
                        "Accept-Language": "pl,en;q=0.9",
                        "Referer": "https://www.siepomaga.pl/",
                    },
                ),
                timeout=15.0,
            )
            resp.raise_for_status()
            data = await resp.json()
            result = _parse_api_response(data, self.url, self.slug)
            if result is not None:
                return result
        except asyncio.TimeoutError as err:
            msg = f"Timeout ładowania API: {api_url}"
            if log_errors:
                _LOGGER.warning("%s", msg)
            raise UpdateFailed(msg) from err
        except Exception as err:
            if log_errors:
                _LOGGER.exception("Błąd API %s: %s", api_url, err)
            raise UpdateFailed(f"Błąd API: {err}") from err

        raise UpdateFailed("API nie zwróciło danych zbiórki")
