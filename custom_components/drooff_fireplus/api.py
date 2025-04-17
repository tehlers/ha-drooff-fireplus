"""Sample API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout


class FireplusApiClientError(Exception):
    """Exception to indicate a general API error."""


class FireplusApiClientCommunicationError(
    FireplusApiClientError,
):
    """Exception to indicate a communication error."""


class FireplusApiClient:
    """Drooff fire+ API Client."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Drooff fire+ API Client."""
        self._host = host
        self._session = session

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        return FireplusData(
            await self._api_wrapper(
                method="get",
                url=f"http://{self._host}/php/easpanel.php",
            ),
            await self._api_wrapper(
                method="get",
                url=f"http://{self._host}/php/easkonfig.php",
            ),
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                )
                response.raise_for_status()
                return await response.text()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise FireplusApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise FireplusApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise FireplusApiClientError(
                msg,
            ) from exception


class FireplusData:
    """Stores the metrics and data retrieved from the Drooff fire+ API."""

    temperature: int
    air_slider: float
    draught: float
    operating_time: int

    def __init__(self, panel_response: str, configuration_response: str) -> None:
        """Metrics and data retrieved from the Drooff fire+ API."""
        panel_values = panel_response[2:-1].split("\\n")

        self.temperature = int(panel_values[5])
        self.air_slider = float(panel_values[6])
        self.draught = float(panel_values[7])

        configuration_values = configuration_response[2:-1].split("\\n")

        self.operating_time = int(configuration_values[7])
