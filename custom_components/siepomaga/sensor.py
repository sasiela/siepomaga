"""Sensor platform for SiePomaga integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_SLUG, ATTR_TITLE, ATTR_URL, DOMAIN
from .coordinator import SiePomagaCoordinator


@dataclass(frozen=True, kw_only=True)
class SiePomagaSensorEntityDescription(SensorEntityDescription):
    """Describes a SiePomaga sensor entity."""


SENSOR_DESCRIPTIONS: tuple[SiePomagaSensorEntityDescription, ...] = (
    SiePomagaSensorEntityDescription(
        key="raised",
        name="Zebrano",
        icon="mdi:hand-coin",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
    ),
    SiePomagaSensorEntityDescription(
        key="missing",
        name="Brakuje",
        icon="mdi:cash-minus",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
    ),
    SiePomagaSensorEntityDescription(
        key="goal",
        name="Cel",
        icon="mdi:target",
        native_unit_of_measurement="PLN",
        device_class=SensorDeviceClass.MONETARY,
    ),
    SiePomagaSensorEntityDescription(
        key="percent",
        name="Postęp",
        icon="mdi:percent",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SiePomagaSensorEntityDescription(
        key="supporters",
        name="Wspierających",
        icon="mdi:account-group",
        native_unit_of_measurement="osób",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SiePomagaSensorEntityDescription(
        key="steady_supporters",
        name="Stałych pomagaczy",
        icon="mdi:account-heart",
        native_unit_of_measurement="osób",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SiePomagaSensorEntityDescription(
        key="start_date",
        name="Rozpoczęcie",
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.DATE,
    ),
    SiePomagaSensorEntityDescription(
        key="end_date",
        name="Zakończenie",
        icon="mdi:calendar-end",
        device_class=SensorDeviceClass.DATE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for a config entry."""
    coordinator: SiePomagaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[0], "raised_pln"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[1], "missing_pln"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[2], "goal_pln"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[3], "percent"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[4], "supporters"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[5], "steady_supporters"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[6], "start_date"),
            SiePomagaFundraiserSensor(coordinator, entry, SENSOR_DESCRIPTIONS[7], "end_date"),
        ]
    )


class SiePomagaFundraiserSensor(CoordinatorEntity[SiePomagaCoordinator], SensorEntity):
    """A sensor backed by the SiePomaga coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SiePomagaCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        data_attr: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._data_attr = data_attr

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.slug)},
            name=f"SiePomaga {self.coordinator.slug}",
            configuration_url=self.coordinator.url,
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        if data is None:
            return None
        value = getattr(data, self._data_attr)
        # Dla device_class DATE HA oczekuje obiektu date, nie stringa (sam wywoła .isoformat())
        return value

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        if data is None:
            return {}
        return {
            ATTR_URL: data.url,
            ATTR_SLUG: data.slug,
            ATTR_TITLE: data.title,
        }

