"""DataUpdateCoordinator for Meteo.lt integration."""

from __future__ import annotations

import logging

import aiohttp
from meteo_lt import Forecast as MeteoLtForecast, MeteoLtAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type MeteoLtConfigEntry = ConfigEntry[MeteoLtUpdateCoordinator]


class MeteoLtUpdateCoordinator(DataUpdateCoordinator[MeteoLtForecast]):
    """Class to manage fetching Meteo.lt data."""

    def __init__(
        self,
        hass: HomeAssistant,
        place_code: str,
        config_entry: MeteoLtConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.client = MeteoLtAPI()
        self.place_code = place_code

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> MeteoLtForecast:
        """Fetch data from Meteo.lt API."""
        try:
            forecast = await self.client.get_forecast(self.place_code)
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(
                f"API returned error status {err.status}: {err.message}"
            ) from err
        except aiohttp.ClientConnectionError as err:
            raise UpdateFailed(f"Cannot connect to API: {err}") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # Check if forecast data is available
        if not forecast.forecast_timestamps:
            raise UpdateFailed(
                f"No forecast data available for {self.place_code} - API returned empty timestamps"
            )

        return forecast
