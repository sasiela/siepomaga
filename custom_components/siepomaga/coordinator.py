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


# React Router (siepomaga.pl): dane w streamController.enqueue("...")
def _extract_enqueue_payloads(text: str) -> list[str]:
    """Wyciągnij stringi z wywołań .enqueue("...") w HTML."""
    out: list[str] = []
    i = 0
    while True:
        # Szukaj .enqueue(" lub enqueue("
        idx = text.find("enqueue(", i)
        if idx < 0:
            break
        idx = idx + len("enqueue(")
        # Pomijamy białe znaki
        while idx < len(text) and text[idx] in " \t\n\r":
            idx += 1
        if idx >= len(text):
            break
        quote = text[idx]
        if quote not in ("'", '"'):
            i = idx + 1
            continue
        idx += 1
        start = idx
        buf: list[str] = []
        while idx < len(text):
            c = text[idx]
            if c == "\\" and idx + 1 < len(text):
                buf.append(text[idx : idx + 2])
                idx += 2
                continue
            if c == quote:
                out.append("".join(buf))
                idx += 1
                break
            buf.append(c)
            idx += 1
        else:
            break
        i = idx
    return out


# Next.js: atrybuty mogą być w dowolnej kolejności
_RE_NEXT_DATA = re.compile(
    r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*type=["\']application/json["\'][^>]*>(.*?)</script>'
    r'|<script[^>]*type=["\']application/json["\'][^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _to_num(v: object) -> int | None:
    if v is None: return None
    if isinstance(v, (int, float)) and v >= 0: return int(v)
    if isinstance(v, str) and v.replace(" ", "").replace("\u00a0", "").isdigit():
        return int(v.replace(" ", "").replace("\u00a0", ""))
    return None


def _extract_from_dict(c: dict, url: str, slug: str) -> FundraiserData | None:
    """Jeśli dict ma raised/goal-like pola, zwróć FundraiserData."""
    raised = None
    for k in ("raised", "collected", "amountCollected", "sum", "amount", "raisedAmount", "totalAmount"):
        raised = _to_num(c.get(k))
        if raised is not None: break
    goal = None
    for k in ("goal", "target", "amountGoal", "goalAmount", "total", "requiredAmount"):
        goal = _to_num(c.get(k))
        if goal is not None: break
    if raised is None and goal is None:
        return None
    percent = None
    for k in ("percent", "percentage", "progress", "progressPercent"):
        v = c.get(k)
        if isinstance(v, (int, float)) and 0 <= v <= 100:
            percent = float(v)
            break
    supporters = None
    for k in ("supporters", "donors", "donorsCount", "supportersCount"):
        supporters = _to_num(c.get(k))
        if supporters is not None: break
    steady = None
    for k in ("steadySupporters", "steady_supporters", "permanentSupportersCount"):
        steady = _to_num(c.get(k))
        if steady is not None: break
    if goal is None and raised and percent: goal = int(raised / (percent / 100.0))
    if raised is None and goal and percent is not None: raised = int(goal * (percent / 100.0))
    missing = (goal - raised) if (goal is not None and raised is not None) else None
    return FundraiserData(raised_pln=raised, missing_pln=missing, goal_pln=goal, percent=percent, supporters=supporters, steady_supporters=steady, start_date=None, end_date=None, title=None, url=url, slug=slug)


def _walk_json(obj: object, url: str, slug: str) -> FundraiserData | None:
    if isinstance(obj, dict):
        out = _extract_from_dict(obj, url, slug)
        if out is not None: return out
        for v in obj.values():
            out = _walk_json(v, url, slug)
            if out is not None: return out
    elif isinstance(obj, list):
        for item in obj:
            out = _walk_json(item, url, slug)
            if out is not None: return out
    return None


def _parse_react_router_stream(text: str, url: str, slug: str) -> FundraiserData | None:
    """Siepomaga.pl używa React Router – dane w streamController.enqueue("...")."""
    for payload in _extract_enqueue_payloads(text):
        payload = payload.strip()
        if len(payload) < 10:
            continue
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            continue
        result = _walk_json(data, url, slug)
        if result is not None:
            return result
    return None


def _parse_next_data(text: str, url: str, slug: str, log_errors: bool = False) -> FundraiserData | None:
    """Wyciągnij dane z __NEXT_DATA__ (Next.js) gdy w HTML nie ma 'zł'."""
    m = _RE_NEXT_DATA.search(text)
    if not m:
        return None
    json_str = (m.group(1) or m.group(2) or "").strip()
    if not json_str:
        return None
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None
    result = _walk_json(data, url, slug)
    if result is not None:
        return result
    if log_errors and isinstance(data, dict):
        _LOGGER.info("SiePomaga __NEXT_DATA__ (brak dopasowania): keys=%s", list(data.keys())[:20])
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

        # W JSON "zł" bywa jako \u017a\u0142 – zdekoduj i sprawdź ponownie
        if "zł" not in text and "\\u017a" in text and "\\u0142" in text:
            try:
                text = text.encode("utf-8").decode("unicode_escape")
            except Exception:
                pass
        # Strona może zwrócić szkielet (bez "zł") – spróbuj __NEXT_DATA__, React Router stream, lub zgłoś błąd
        if "zł" not in text or len(text.strip()) < 500:
            next_data = _parse_next_data(text, self.url, self.slug, log_errors)
            if next_data is not None:
                return next_data
            # siepomaga.pl: React Router, dane w enqueue("...")
            stream_data = _parse_react_router_stream(text, self.url, self.slug)
            if stream_data is not None:
                return stream_data
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

