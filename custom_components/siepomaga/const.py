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

USER_AGENT = (
    "Mozilla/5.0 (compatible; HomeAssistant-SiePomaga/1.0; +https://github.com/sasiela/siepomaga)"
)

