"""Sensor platform for Insite Energy."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import InsiteEnergyCoordinator
from .const import DOMAIN

SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="active_balance",
        name="Active Balance",
        icon="mdi:currency-gbp",
        native_unit_of_measurement="GBP",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="debt_balance",
        name="Debt Balance",
        icon="mdi:currency-gbp",
        native_unit_of_measurement="GBP",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="debt_recovery_rate",
        name="Debt Recovery Rate",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="unit_rate_pence",
        name="Unit Rate",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement="p/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="standing_charge_pence",
        name="Standing Charge",
        icon="mdi:calendar-today",
        native_unit_of_measurement="p/day",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="last_meter_reading_date",
        name="Last Meter Reading",
        icon="mdi:meter-electric",
        device_class=None,
    ),
    SensorEntityDescription(
        key="meter_out_of_comms",
        name="Meter Out of Comms",
        icon="mdi:wifi-off",
        device_class=SensorDeviceClass.ENUM,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Insite Energy sensors."""
    coordinator: InsiteEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        InsiteEnergySensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.append(InsiteEnergyLastPollSensor(coordinator, entry))
    entities.append(InsiteEnergyNextPollSensor(coordinator, entry))
    async_add_entities(entities)


class InsiteEnergySensor(CoordinatorEntity[InsiteEnergyCoordinator], SensorEntity):
    """Representation of an Insite Energy sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InsiteEnergyCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Insite Energy",
        manufacturer="Insite Energy",
        model="Guru Prepay Meter",
        configuration_url="https://my.insite-energy.co.uk/Customer/Details",
    )


class InsiteEnergyLastPollSensor(CoordinatorEntity[InsiteEnergyCoordinator], SensorEntity):
    """Sensor showing when data was last fetched."""

    _attr_has_entity_name = True
    _attr_name = "Last Poll Time"
    _attr_icon = "mdi:clock-check"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: InsiteEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_poll_time"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_poll_time


class InsiteEnergyNextPollSensor(CoordinatorEntity[InsiteEnergyCoordinator], SensorEntity):
    """Sensor showing when the next data fetch is scheduled."""

    _attr_has_entity_name = True
    _attr_name = "Next Poll Time"
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: InsiteEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_next_poll_time"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> datetime | None:
        if self.coordinator.last_poll_time is None:
            return None
        return self.coordinator.last_poll_time + self.coordinator.update_interval
