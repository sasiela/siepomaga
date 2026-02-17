"""Constants for the SiePomaga integration."""

from homeassistant.const import Platform

DOMAIN = "siepomaga"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_FUNDRAISER = "fundraiser"
CONF_URL = "url"
CONF_SLUG = "slug"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 300  # seconds

ATTR_URL = "url"
ATTR_SLUG = "slug"
ATTR_TITLE = "title"

USER_AGENT = "Home Assistant (SiePomaga integration)"

