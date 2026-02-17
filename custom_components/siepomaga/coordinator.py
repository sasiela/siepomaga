"""Data update coordinator for SiePomaga integration."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
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


_RE_NEXT_DATA = re.compile(
    r'<script\s+id="__NEXT_DATA__"\s+type="application/json"\s*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _parse_next_data(text: str, url: str, slug: str) -> FundraiserData | None:
    """Wyciągnij dane z __NEXT_DATA__ (Next.js) gdy w HTML nie ma 'zł'."""
    m = _RE_NEXT_DATA.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except (json.JSONDecodeError, TypeError):
        return None
    # Typowe ścieżki w Next.js: props.pageProps.* lub props.*
    props = data.get("props") or {}
    page_props = props.get("pageProps") if isinstance(props, dict) else {}
    if not isinstance(page_props, dict):
        page_props = {}
    # Szukaj w pageProps i jednym poziomie w głąb (fundraiser, campaign, collection)
    for node in [page_props, data]:
        if not isinstance(node, dict):
            continue
        for candidate in node.values():
            if not isinstance(candidate, dict):
                continue
            # Kwoty: raised/collected/amountCollected/sum, goal/target/amountGoal
            raised = None
            for k in ("raised", "collected", "amountCollected", "sum", "amount", "raisedAmount"):
                v = candidate.get(k)
                if isinstance(v, (int, float)) and v >= 0:
                    raised = int(v)
                    break
                if isinstance(v, str) and v.replace(" ", "").isdigit():
                    raised = int(v.replace(" ", ""))
                    break
            goal = None
            for k in ("goal", "target", "amountGoal", "goalAmount", "total"):
                v = candidate.get(k)
                if isinstance(v, (int, float)) and v >= 0:
                    goal = int(v)
                    break
                if isinstance(v, str) and v.replace(" ", "").isdigit():
                    goal = int(v.replace(" ", ""))
                    break
            percent = None
            for k in ("percent", "percentage", "progress"):
                v = candidate.get(k)
                if isinstance(v, (int, float)) and 0 <= v <= 100:
                    percent = float(v)
                    break
            supporters = None
            for k in ("supporters", "donors", "donorsCount", "backersCount", "count"):
                v = candidate.get(k)
                if isinstance(v, (int, float)) and v >= 0:
                    supporters = int(v)
                    break
            steady = None
            for k in ("steadySupporters", "steady_supporters", "regularSupporters"):
                v = candidate.get(k)
                if isinstance(v, (int, float)) and v >= 0:
                    steady = int(v)
                    break
            if raised is not None or goal is not None:
                if goal is None and raised is not None and percent is not None and percent > 0:
                    goal = int(raised / (percent / 100.0)) if percent else None
                if raised is None and goal is not None and percent is not None:
                    raised = int(goal * (percent / 100.0)) if percent else None
                missing = (goal - raised) if (goal is not None and raised is not None) else None
                return FundraiserData(
                    raised_pln=raised,
                    missing_pln=missing,
                    goal_pln=goal,
                    percent=percent,
                    supporters=supporters,
                    steady_supporters=steady,
                    start_date=None,
                    end_date=None,
                    title=None,
                    url=url,
                    slug=slug,
                )
    return None


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
        self._log_errors_default = bool(options.get(CONF_LOG_ERRORS, DEFAULT_LOG_ERRORS))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"SiePomaga {self.slug}",
            update_interval=timedelta(seconds=scan_interval),
        )

    def _log_errors(self) -> bool:
        """Use current option (so change takes effect without reload)."""
        opts = self.entry.options or {}
        return bool(opts.get(CONF_LOG_ERRORS, self._log_errors_default))

    async def _async_update_data(self) -> FundraiserData:
        session = async_get_clientsession(self.hass)
        log_errors = self._log_errors()

        try:
            resp = await asyncio.wait_for(
                session.get(
                    self.url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "pl,en;q=0.9",
                        "Referer": "https://www.siepomaga.pl/",
                    },
                ),
                timeout=20.0,
            )
            resp.raise_for_status()
            text = await resp.text(encoding="utf-8", errors="replace")
        except asyncio.TimeoutError as err:
            if log_errors:
                _LOGGER.exception("Timeout loading %s", self.url)
            else:
                _LOGGER.warning("Timeout loading %s", self.url)
            raise UpdateFailed(f"Timeout loading {self.url}") from err
        except Exception as err:
            if log_errors:
                _LOGGER.exception("Request failed for %s: %s", self.url, err)
            else:
                _LOGGER.warning("Request failed for %s: %s", self.url, err)
            raise UpdateFailed(f"Request failed: {err}") from err

        # Strona może zwrócić szkielet (bez "zł") – najpierw spróbuj wyciągnąć dane z __NEXT_DATA__
        if "zł" not in text or len(text.strip()) < 500:
            next_data = _parse_next_data(text, self.url, self.slug)
            if next_data is not None:
                return next_data
            msg = (
                f"Odpowiedź z {self.url} wygląda na niepełną (brak 'zł' lub bardzo krótka). "
                "Włącz 'Zapisuj błędy do logów' w opcjach po szczegóły."
            )
            _LOGGER.warning("%s Długość odpowiedzi: %d znaków.", msg, len(text))
            if log_errors:
                _LOGGER.error("Początek odpowiedzi: %s", text[:400].replace("\n", " "))
            raise UpdateFailed(msg)

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

