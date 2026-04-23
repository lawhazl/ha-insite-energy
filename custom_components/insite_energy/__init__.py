"""Insite Energy integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import InsiteEnergyAPI, InsiteEnergyAuthError, InsiteEnergyError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Insite Energy from a config entry."""
    api = InsiteEnergyAPI(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = InsiteEnergyCoordinator(hass, api, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class InsiteEnergyCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch Insite Energy data."""

    def __init__(self, hass: HomeAssistant, api: InsiteEnergyAPI, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )
        self.api = api
        self.last_poll_time: datetime | None = None

    async def _async_update_data(self):
        """Fetch data from Insite Energy."""
        try:
            data = await self.hass.async_add_executor_job(self.api.fetch_data)
            self.last_poll_time = dt_util.utcnow()
            return data
        except InsiteEnergyAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except InsiteEnergyError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
