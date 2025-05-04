"""Sample API Client."""

from __future__ import annotations

import socket
from enum import Enum, auto
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
        return FireplusResponse(
            await self._api_wrapper(
                method="get",
                url=f"http://{self._host}/php/easpanel.php",
            ),
            await self._api_wrapper(
                method="get",
                url=f"http://{self._host}/php/easkonfig.php",
            ),
        )

    async def async_update_settings(
        self,
        brightness: int | None = None,
        volume: int | None = None,
        ember_burndown: bool | None = None,
        burn_rate: int | None = None,
    ) -> None:
        """Update settings of Drooff fire+."""
        current_data = await self.async_get_data()
        burn_rate_values = _get_values_for_burn_rate(burn_rate if burn_rate is not None else current_data.burn_rate)

        data = {
            "Betrieb": burn_rate_values[0],
            "Leistung": burn_rate_values[1],
            "Helligkeit": brightness if brightness is not None else current_data.brightness,
            "Bedienung": int(current_data.web_controls_shown),
            "AB": int(ember_burndown if ember_burndown is not None else current_data.ember_burndown),
            "Lautstaerke": volume if volume is not None else current_data.volume,
            "CNT": (current_data.count + 1) % 100,
        }

        await self._api_wrapper(method="post", url=f"http://{self._host}/php/easpanelW.php", data=data)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    data=data,
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


class FireplusResponse:
    """Stores the metrics and data retrieved from the Drooff fire+ API."""

    brightness: int
    volume: int
    temperature: int
    max_temperature: int
    air_slider: float
    chimney_draught: float
    operation_mode: FireplusOperationMode
    error: FireplusError
    count: int
    operating_time: int
    chimney_draught_available: bool
    ember_burndown: bool
    heating_progress: float
    web_controls_shown: bool
    burn_rate: int

    def __init__(self, panel_response: str, configuration_response: str) -> None:
        """Metrics and data retrieved from the Drooff fire+ API."""
        panel_values = panel_response[2:-1].split("\\n")

        self.web_controls_shown = panel_values[1] == "1"
        self.brightness = int(panel_values[4])
        self.volume = int(panel_values[12])
        self.temperature = int(panel_values[5])
        self.air_slider = float(panel_values[6])
        self.chimney_draught = float(panel_values[7])
        self.operation_mode = _get_operation_mode(panel_values[8])
        self.error = _get_error(int(panel_values[9]))
        self.ember_burndown = panel_values[10] == "1"
        self.count = int(panel_values[16])
        self.burn_rate = _get_burn_rate(int(panel_values[2]), int(panel_values[3]))

        configuration_values = configuration_response[2:-1].split("\\n")

        self.max_temperature = int(configuration_values[1])
        self.chimney_draught_available = configuration_values[4] == "1"
        self.operating_time = int(configuration_values[7])

        self.heating_progress = (int(panel_values[11]) / int(configuration_values[6])) * 100


class FireplusOperationMode(Enum):
    """Operation modes of the Drooff fire+ combustion control system."""

    UNKNOWN = auto()
    STANDBY = auto()
    REGULAR = auto()
    HEATING = auto()
    WOOD_REQUIRED = auto()
    WOOD_URGENTLY_REQUIRED = auto()
    EMBER_PRESERVATION = auto()
    EMBER_BURNDOWN = auto()
    ERROR = auto()


# Lookup table of LED states to operation modes
_OPERATION_MODE_LOOKUP = {
    "aus": FireplusOperationMode.STANDBY,
    "Gruen": FireplusOperationMode.REGULAR,
    "Gruen blinkt": FireplusOperationMode.HEATING,
    "Gelb": FireplusOperationMode.WOOD_REQUIRED,
    "Gelb blinkt": FireplusOperationMode.WOOD_URGENTLY_REQUIRED,
    "Violett dunkel": FireplusOperationMode.EMBER_PRESERVATION,
    "Orange": FireplusOperationMode.EMBER_BURNDOWN,
    "Rot blinkt": FireplusOperationMode.ERROR,
}


def _get_operation_mode(led_state: str) -> FireplusOperationMode:
    return _OPERATION_MODE_LOOKUP.get(led_state, FireplusOperationMode.UNKNOWN)


# Lookup table of burn rate to values for "Betrieb" and "Leistung"
_BURN_RATE_LOOKUP = {1: (2, 4), 2: (3, 4), 3: (4, 4), 4: (2, 8), 5: (3, 8), 6: (4, 8)}


def _get_values_for_burn_rate(burn_rate: int) -> (int, int):
    return _BURN_RATE_LOOKUP.get(burn_rate, (2, 4))


# Lookup table of values for "Betrieb" and "Leistung" to burn rate
_DERIVED_BURN_RATE_LOOKUP = {value: key for key, value in _BURN_RATE_LOOKUP.items()}


def _get_burn_rate(betrieb: int, leistung: int) -> int:
    return _DERIVED_BURN_RATE_LOOKUP.get((betrieb, leistung), 1)


class FireplusError(Enum):
    """Errors of the Drooff fire+ combustion control system."""

    NONE = auto()
    TEMPERATURE_SENSOR_DEFECTIVE = auto()
    PRESSURE_MEASUREMENT_DEFECTIVE = auto()
    AIR_SLIDER_DEFECTIVE = auto()
    SERVICE_MODE_ENABLED = auto()
    CHIMNEY_DRAUGHT_TOO_LOW = auto()
    AIR_SLIDER_STUCK = auto()
    NO_CHIMNEY_DRAUGHT = auto()
    WRONG_MOTOR_DIRECTION = auto()
    UNKNOWN = auto()


# Lookup table of error codes to errors
_ERROR_LOOKUP = {
    0: FireplusError.NONE,
    1: FireplusError.TEMPERATURE_SENSOR_DEFECTIVE,
    2: FireplusError.PRESSURE_MEASUREMENT_DEFECTIVE,
    3: FireplusError.AIR_SLIDER_DEFECTIVE,
    4: FireplusError.SERVICE_MODE_ENABLED,
    5: FireplusError.CHIMNEY_DRAUGHT_TOO_LOW,
    6: FireplusError.AIR_SLIDER_STUCK,
    7: FireplusError.TEMPERATURE_SENSOR_DEFECTIVE,
    8: FireplusError.TEMPERATURE_SENSOR_DEFECTIVE,
    9: FireplusError.NO_CHIMNEY_DRAUGHT,
    10: FireplusError.WRONG_MOTOR_DIRECTION,
}


def _get_error(error_code: int) -> FireplusError:
    return _ERROR_LOOKUP.get(error_code, FireplusError.UNKNOWN)
