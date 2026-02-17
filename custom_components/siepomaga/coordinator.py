"""Data update coordinator for SiePomaga integration."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SLUG,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FundraiserData:
    """Parsed fundraiser data."""

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


_RE_RAISED_WITH_PERCENT_LINE = re.compile(
    r"([0-9][0-9\s\u00A0]*[0-9])\s*zł\s*\(\s*([0-9]+,[0-9]+)%\s*\)",
    re.IGNORECASE,
)
_RE_RAISED_PLAIN_LINE = re.compile(r"([0-9][0-9\s\u00A0]*[0-9])\s*zł\b", re.IGNORECASE)
_RE_MISSING = re.compile(r"Brakuje\s*([0-9\s\u00A0]+)\s*zł", re.IGNORECASE)
_RE_PERCENT = re.compile(r"\(\s*([0-9]+,[0-9]+)%\s*\)")
_RE_SUPPORTERS = re.compile(
    r"Wspar\w*\s*([0-9\s\u00A0]+)\s*(?:osob(?:a|y)|osób)",
    re.IGNORECASE,
)
_RE_STEADY_SUPPORTERS = re.compile(r"([0-9\s\u00A0]+)\s*Stałych\s+Pomagaczy", re.IGNORECASE)
_RE_START = re.compile(r"Rozpoczęcie:\s*([0-9]{1,2})\s+([^\s]+)\s+([0-9]{4})", re.IGNORECASE)
_RE_END = re.compile(r"Zakończenie:\s*([0-9]{1,2})\s+([^\s]+)\s+([0-9]{4})", re.IGNORECASE)
_RE_TITLE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)

_PL_MONTHS: dict[str, int] = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "wrzesnia": 9,  # fallback without diacritics
    "października": 10,
    "pazdziernika": 10,  # fallback without diacritics
    "listopada": 11,
    "grudnia": 12,
}


def _to_int_pln(s: str | None) -> int | None:
    if not s:
        return None
    return int(s.replace(" ", "").replace("\u00A0", ""))


def _to_float_percent(s: str | None) -> float | None:
    if not s:
        return None
    return float(s.replace(",", "."))


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    # Return first non-None group (handles patterns with multiple groups)
    for i in range(1, m.lastindex + 1 if m.lastindex else 1):
        if m.group(i) is not None:
            return m.group(i)
    return m.group(1) if m.lastindex else None

def _to_date_pl(day_s: str | None, month_s: str | None, year_s: str | None) -> date | None:
    if not (day_s and month_s and year_s):
        return None
    try:
        day = int(day_s)
        year = int(year_s)
        month = _PL_MONTHS.get(month_s.strip().lower())
        if not month:
            return None
        return date(year, month, day)
    except Exception:
        return None


class SiePomagaCoordinator(DataUpdateCoordinator[FundraiserData]):
    """Fetch and parse fundraiser data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.slug: str = entry.data[CONF_SLUG]
        self.url: str = entry.data[CONF_URL]
        options = entry.options or {}
        scan_interval = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"SiePomaga {self.slug}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> FundraiserData:
        session = async_get_clientsession(self.hass)

        try:
            resp = await asyncio.wait_for(
                session.get(self.url, headers={"User-Agent": USER_AGENT}),
                timeout=20.0,
            )
            resp.raise_for_status()
            text = await resp.text()
        except asyncio.TimeoutError as err:
            _LOGGER.warning("Timeout loading %s", self.url)
            raise UpdateFailed(f"Timeout loading {self.url}") from err
        except Exception as err:
            _LOGGER.warning("Request failed for %s: %s", self.url, err)
            raise UpdateFailed(f"Request failed: {err}") from err

        # Find raised + percent.
        # Active fundraisers usually contain: "<amount> zł(<percent>%)"
        # Finished campaigns often contain only: "<amount> zł" (no percent, no "Brakuje").
        raised: int | None = None
        percent: float | None = None
        lines = text.split("\n")

        for line in lines:
            if "Zakończenie:" in line or "Rozpoczęcie:" in line:
                continue
            match = _RE_RAISED_WITH_PERCENT_LINE.search(line)
            if match:
                raised = _to_int_pln(match.group(1).strip())
                percent = _to_float_percent(match.group(2).strip())
                break

        if raised is None:
            _LOGGER.debug(
                "No 'zł(percent)' line found for %s; trying plain 'zł' line",
                self.url,
            )
            for line in lines:
                if "Zakończenie:" in line or "Rozpoczęcie:" in line:
                    continue
                if "Brakuje" in line:
                    continue
                if "Koszt" in line:
                    continue
                match = _RE_RAISED_PLAIN_LINE.search(line)
                if match:
                    raised = _to_int_pln(match.group(1).strip())
                    break

        missing = _to_int_pln(_first_group(_RE_MISSING, text))
        goal = (raised + missing) if (raised is not None and missing is not None) else None
        if percent is None:
            percent = _to_float_percent(_first_group(_RE_PERCENT, text))
        supporters = _to_int_pln(_first_group(_RE_SUPPORTERS, text))
        steady_supporters = _to_int_pln(_first_group(_RE_STEADY_SUPPORTERS, text))

        start_m = _RE_START.search(text)
        start_date = (
            _to_date_pl(start_m.group(1), start_m.group(2), start_m.group(3)) if start_m else None
        )
        end_m = _RE_END.search(text)
        end_date = _to_date_pl(end_m.group(1), end_m.group(2), end_m.group(3)) if end_m else None

        title = None
        raw_title = _first_group(_RE_TITLE, text)
        if raw_title:
            title = re.sub(r"\s+", " ", raw_title).strip()

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
            url=self.url,
            slug=self.slug,
        )

