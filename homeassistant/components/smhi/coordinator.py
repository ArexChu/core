"""DataUpdateCoordinator for the SMHI integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pysmhi import (
    SMHIFireForecast,
    SmhiFireForecastException,
    SMHIFirePointForecast,
    SMHIForecast,
    SmhiForecastException,
    SMHIPointForecast,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER, TIMEOUT

type SMHIConfigEntry = ConfigEntry[SMHIDataUpdateCoordinator]


@dataclass
class SMHIForecastData:
    """Dataclass for SMHI data."""

    daily: list[SMHIForecast]
    hourly: list[SMHIForecast]
    twice_daily: list[SMHIForecast]
    fire_daily: list[SMHIFireForecast]
    fire_hourly: list[SMHIFireForecast]


class SMHIDataUpdateCoordinator(DataUpdateCoordinator[SMHIForecastData]):
    """A SMHI Data Update Coordinator."""

    config_entry: SMHIConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: SMHIConfigEntry) -> None:
        """Initialize the SMHI coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._smhi_api = SMHIPointForecast(
            config_entry.data[CONF_LOCATION][CONF_LONGITUDE],
            config_entry.data[CONF_LOCATION][CONF_LATITUDE],
            session=aiohttp_client.async_get_clientsession(hass),
        )
        self._smhi_fire_api = SMHIFirePointForecast(
            config_entry.data[CONF_LOCATION][CONF_LONGITUDE],
            config_entry.data[CONF_LOCATION][CONF_LATITUDE],
            session=aiohttp_client.async_get_clientsession(hass),
        )

    async def _async_update_data(self) -> SMHIForecastData:
        """Fetch data from SMHI."""
        try:
            async with asyncio.timeout(TIMEOUT):
                _forecast_daily = await self._smhi_api.async_get_daily_forecast()
                _forecast_hourly = await self._smhi_api.async_get_hourly_forecast()
                _forecast_twice_daily = (
                    await self._smhi_api.async_get_twice_daily_forecast()
                )
                _forecast_fire_daily = (
                    await self._smhi_fire_api.async_get_daily_forecast()
                )
                _forecast_fire_hourly = (
                    await self._smhi_fire_api.async_get_hourly_forecast()
                )
        except (SmhiForecastException, SmhiFireForecastException) as ex:
            raise UpdateFailed(
                "Failed to retrieve the forecast from the SMHI API"
            ) from ex

        return SMHIForecastData(
            daily=_forecast_daily,
            hourly=_forecast_hourly,
            twice_daily=_forecast_twice_daily,
            fire_daily=_forecast_fire_daily,
            fire_hourly=_forecast_fire_hourly,
        )

    @property
    def current(self) -> SMHIForecast:
        """Return the current metrics."""
        return self.data.daily[0]

    @property
    def fire_current(self) -> SMHIFireForecast:
        """Return the current fire metrics."""
        return self.data.fire_daily[0]
