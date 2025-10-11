"""Drooff fire+ API Client."""

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


class FireplusApiClientInvalidResponseError(
    FireplusApiClientError,
):
    """Exception to indicate that the response contained invalid data."""


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
        *,
        brightness: int | None = None,
        volume: int | None = None,
        ember_burndown: bool | None = None,
        burn_rate: int | None = None,
        led: bool | None = None,
    ) -> None:
        """Update settings of Drooff fire+."""
        current_data = await self.async_get_data()

        if current_data.version == 1:
            burn_rate_values = _get_values_for_burn_rate_v1(
                burn_rate if burn_rate is not None else current_data.burn_rate
            )

            data = {
                "Betrieb": burn_rate_values[0],
                "Leistung": burn_rate_values[1],
                "Helligkeit": brightness if brightness is not None else current_data.brightness,
                "Bedienung": int(current_data.web_controls_shown),
                "LED": int(led if led is not None else current_data.led),
                "AB": int(ember_burndown if ember_burndown is not None else current_data.ember_burndown),
            }
        else:
            burn_rate_values = _get_values_for_burn_rate_v2(
                burn_rate if burn_rate is not None else current_data.burn_rate
            )

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
    volume: int | None
    temperature: int
    max_temperature: int
    air_slider: float
    chimney_draught: float
    operation_status: FireplusOperationStatus
    error: FireplusError
    error_code: int
    count: int
    operating_time: int | None
    chimney_draught_available: bool
    ember_burndown: bool
    heating_progress: float
    web_controls_shown: bool
    burn_rate: int
    serial_number: str
    led: bool | None
    version: int

    def __init__(self, panel_response: str, configuration_response: str) -> None:
        """Metrics and data retrieved from the Drooff fire+ API."""
        try:
            panel_values = panel_response[2:-1].split("\\n")
            configuration_values = configuration_response[2:-1].split("\\n")

            self.version = int(configuration_values[0].split(".")[0])

            self.web_controls_shown = panel_values[1] == "1"
            self.brightness = int(panel_values[4])
            self.temperature = int(panel_values[5])
            self.air_slider = float(panel_values[6])
            self.chimney_draught = float(panel_values[7])
            self.operation_status = _get_operation_status(panel_values[8])
            self.error = _get_error(int(panel_values[9]))
            self.error_code = int(panel_values[9])

            self.max_temperature = int(configuration_values[1])
            # In the source code of the fire+ webapp, the value is called 'hardware version'.
            # As it looks more like a serial number, we use it as such for the time being, in
            # particular to make it part of the unique id.
            self.serial_number = configuration_values[3]
            self.chimney_draught_available = configuration_values[4] == "1"

            if self.version == 1:
                self.__init_version1(panel_values, configuration_values)
            else:
                self.__init_version2(panel_values, configuration_values)

        except (IndexError, ValueError) as exception:
            msg = f"Error parsing responses from fire+: '{panel_response}' and '{configuration_response}'"
            raise FireplusApiClientInvalidResponseError(
                msg,
            ) from exception

    def __init_version1(self, panel_values: list[str], configuration_values: list[str]) -> None:
        self.volume = None
        self.ember_burndown = panel_values[11] == "1"
        self.count = None
        self.led = panel_values[10] == "1"
        self.burn_rate = _get_burn_rate_v1(int(panel_values[2]), int(panel_values[3]))
        self.operating_time = None
        self.heating_progress = (int(panel_values[12]) / int(configuration_values[6])) * 100

    def __init_version2(self, panel_values: list[str], configuration_values: list[str]) -> None:
        self.volume = int(panel_values[12])
        self.ember_burndown = panel_values[10] == "1"
        self.count = int(panel_values[16])
        self.led = None
        self.burn_rate = _get_burn_rate_v2(int(panel_values[2]), int(panel_values[3]))
        self.operating_time = int(configuration_values[7])
        self.heating_progress = (int(panel_values[11]) / int(configuration_values[6])) * 100


class FireplusOperationStatus(Enum):
    """Operation status of the Drooff fire+ combustion control system."""

    UNKNOWN = auto()
    STANDBY = auto()
    REGULAR = auto()
    HEATING = auto()
    WOOD_REQUIRED = auto()
    WOOD_URGENTLY_REQUIRED = auto()
    EMBER_PRESERVATION = auto()
    EMBER_BURNDOWN = auto()
    ERROR = auto()


# Lookup table of LED status to operation status
_OPERATION_STATUS_LOOKUP = {
    "aus": FireplusOperationStatus.STANDBY,
    "Gruen": FireplusOperationStatus.REGULAR,
    "Gruen blinkt": FireplusOperationStatus.HEATING,
    "Gelb": FireplusOperationStatus.WOOD_REQUIRED,
    "Gelb blinkt": FireplusOperationStatus.WOOD_URGENTLY_REQUIRED,
    "Violett dunkel": FireplusOperationStatus.EMBER_PRESERVATION,
    "Orange": FireplusOperationStatus.EMBER_BURNDOWN,
    "Rot blinkt": FireplusOperationStatus.ERROR,
}


def _get_operation_status(led_status: str) -> FireplusOperationStatus:
    return _OPERATION_STATUS_LOOKUP.get(led_status, FireplusOperationStatus.UNKNOWN)


# Lookup table of burn rate to values for "Betrieb" and "Leistung" (API v1)
_BURN_RATE_LOOKUP_V1 = {1: (1, 4), 2: (2, 4), 3: (3, 4), 4: (4, 4), 5: (2, 8), 6: (3, 8), 7: (4, 8)}


# Lookup table of burn rate to values for "Betrieb" and "Leistung" (API v2)
_BURN_RATE_LOOKUP_V2 = {1: (2, 4), 2: (3, 4), 3: (4, 4), 4: (2, 8), 5: (3, 8), 6: (4, 8)}


def _get_values_for_burn_rate_v1(burn_rate: int) -> tuple[int, int]:
    return _BURN_RATE_LOOKUP_V1.get(burn_rate, (1, 4))


def _get_values_for_burn_rate_v2(burn_rate: int) -> tuple[int, int]:
    return _BURN_RATE_LOOKUP_V2.get(burn_rate, (2, 4))


# Lookup table of values for "Betrieb" and "Leistung" to burn rate (API v1)
_DERIVED_BURN_RATE_LOOKUP_V1 = {value: key for key, value in _BURN_RATE_LOOKUP_V1.items()}


# Lookup table of values for "Betrieb" and "Leistung" to burn rate (API v2)
_DERIVED_BURN_RATE_LOOKUP_V2 = {value: key for key, value in _BURN_RATE_LOOKUP_V2.items()}


def _get_burn_rate_v1(betrieb: int, leistung: int) -> int:
    return _DERIVED_BURN_RATE_LOOKUP_V1.get((betrieb, leistung), 1)


def _get_burn_rate_v2(betrieb: int, leistung: int) -> int:
    return _DERIVED_BURN_RATE_LOOKUP_V2.get((betrieb, leistung), 1)


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
