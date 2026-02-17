"""Constants for the SiePomaga integration."""

from homeassistant.const import Platform

DOMAIN = "siepomaga"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_FUNDRAISER = "fundraiser"
CONF_URL = "url"
CONF_SLUG = "slug"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LOG_ERRORS = "log_errors"

DEFAULT_SCAN_INTERVAL = 300  # seconds
DEFAULT_LOG_ERRORS = False

ATTR_URL = "url"
ATTR_SLUG = "slug"
ATTR_TITLE = "title"

# API siepomaga.pl – dane zbiórki w JSON (główne źródło)
API_PERMALINKS_URL = "https://www.siepomaga.pl/api/donor/web/v2/permalinks"

# Wygląda jak przeglądarka, żeby serwer zwracał pełny HTML (nie szkielet bez "zł")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

