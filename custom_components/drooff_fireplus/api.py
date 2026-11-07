"""Drooff fire+ API Client."""

from __future__ import annotations

import asyncio
import json
import socket
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import aiohttp
from awesomeversion import AwesomeVersion

from .const import ETHERNET_LINK

VERSION_2_0_0 = AwesomeVersion("2.0.0")
VERSION_2_4_0 = AwesomeVersion("2.4.0")

# The configuration (version, max. temperature, operating time, ...) changes rarely,
# so it is only requested again after this many seconds.
CONFIGURATION_MAX_AGE = 60

# The configuration of newer web apps has more values (auto update, online support, ...)
CONFIGURATION_EXTRAS = 10

# Values of "FBAutomatik" in the web app
REMOTE_CONTROL_MANUAL = 0
REMOTE_CONTROL_AUTOMATIC = 1
ROOM_CONTROLLER = 3

# Time the fire+ needs before it reports written settings (s)
SETTINGS_DELAY = 1

# Bit in panel value 13 that marks a stove with the Blue Angel label (and an OekoSolve filter)
BLUE_ANGEL_FLAG = 2


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
        self._configuration: str | None = None
        self._configuration_time = 0.0
        self._filter: str | None = None
        self._filter_time = 0.0
        # Every write sends all settings, so writes must not overlap (see async_update_settings)
        self._write_lock = asyncio.Lock()

    async def async_get_data(self, *, fresh: bool = False) -> Any:
        """Get data from the API."""
        panel = await self._api_wrapper(
            method="get",
            url=f"http://{self._host}/php/easpanel.php",
        )
        now = time.monotonic()
        if fresh or self._configuration is None or now - self._configuration_time > CONFIGURATION_MAX_AGE:
            self._configuration = await self._api_wrapper(
                method="get",
                url=f"http://{self._host}/php/easkonfig.php",
            )
            self._configuration_time = now
        data = FireplusResponse(panel, self._configuration)
        if data.blue_angel:
            # only stoves with the Blue Angel label have an OekoSolve filter
            if fresh or self._filter is None or now - self._filter_time > CONFIGURATION_MAX_AGE:
                self._filter_time = now
                try:
                    self._filter = await self._api_wrapper(method="get", url=f"http://{self._host}/php/oeko.php")
                except FireplusApiClientError:
                    # the other values are still valid, the filter status is unknown until the next try
                    self._filter = None
            data = FireplusResponse(panel, self._configuration, self._filter)
        return data

    async def async_get_events(self, since: int) -> str:
        """Get the event log (door and phase changes) since a Unix time, 0 returns the last days."""
        return await self._api_wrapper(method="get", url=f"http://{self._host}/php/easevents.php?id={since}")

    async def async_get_update_status(self) -> FireplusUpdateStatus:
        """Get the result of the last update and when the fire+ looks for updates."""
        result = await self._api_wrapper(method="get", url=f"http://{self._host}/php/UpdateErgebniss.php")
        schedule = await self._api_wrapper(method="get", url=f"http://{self._host}/php/easupdate.php")
        return FireplusUpdateStatus.parse(result, schedule)

    async def async_update_settings(
        self,
        *,
        brightness: int | None = None,
        volume: int | None = None,
        ember_burndown: bool | None = None,
        burn_rate: int | None = None,
        led: bool | None = None,
    ) -> None:
        """
        Update settings of Drooff fire+.

        The fire+ only accepts all settings at once, so the current ones are read first. Writes
        are serialized and wait until the fire+ reports the new values; otherwise a second write
        (for example burn rate and ember burndown in one automation) would read the old values
        and undo the first one.
        """
        async with self._write_lock:
            await self._async_write_settings(
                brightness=brightness,
                volume=volume,
                ember_burndown=ember_burndown,
                burn_rate=burn_rate,
                led=led,
            )
            await asyncio.sleep(SETTINGS_DELAY)

    async def _async_write_settings(
        self,
        *,
        brightness: int | None,
        volume: int | None,
        ember_burndown: bool | None,
        burn_rate: int | None,
        led: bool | None,
    ) -> None:
        current_data = await self.async_get_data(fresh=True)

        if current_data.version >= VERSION_2_0_0:
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
        else:
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

        await self._api_wrapper(method="post", url=f"http://{self._host}/php/easpanelW.php", data=data)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with asyncio.timeout(10):
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
    version: AwesomeVersion
    door_open: bool | None
    weight: float | None
    target_temperature: int | None
    ethernet_link: bool | None
    wifi_signal_strength: int | None
    control_mode: FireplusControlMode | None
    blue_angel: bool
    auto_update: bool | None
    online_support: bool | None
    draught_warning: bool | None
    web_app_version: str | None
    filter_status: FireplusFilterStatus | None
    filter_code: int | None

    def __init__(
        self,
        panel_response: str,
        configuration_response: str,
        filter_response: str | None = None,
    ) -> None:
        """Metrics and data retrieved from the Drooff fire+ API."""
        self._raw = (panel_response, configuration_response)
        if filter_response is not None:
            self._raw = (*self._raw, filter_response)
        try:
            panel_values = panel_response[2:-1].split("\\n")
            configuration_values = configuration_response[2:-1].split("\\n")

            self.version = AwesomeVersion(configuration_values[0])

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
            self.control_mode = None
            self.blue_angel = False
            self.__init_configuration_extras(configuration_values)

            if self.version >= VERSION_2_4_0:
                self.__init_version2_4(panel_values, configuration_values)
            elif self.version >= VERSION_2_0_0:
                self.__init_version2(panel_values, configuration_values)
            else:
                self.__init_version1(panel_values, configuration_values)

        except (IndexError, ValueError) as exception:
            msg = f"Error parsing responses from fire+: '{panel_response}' and '{configuration_response}'"
            raise FireplusApiClientInvalidResponseError(
                msg,
            ) from exception
        self.__init_filter(filter_response)

    def __eq__(self, other: object) -> bool:
        """Responses are equal if the fire+ returned exactly the same data."""
        return isinstance(other, FireplusResponse) and self._raw == other._raw

    __hash__ = None  # type: ignore[assignment]

    @property
    def raw(self) -> tuple[str, ...]:
        """Return the unparsed responses of the fire+ (panel, configuration and filter, if any)."""
        return self._raw

    def __init_filter(self, filter_response: str | None) -> None:
        self.filter_code = None
        self.filter_status = None
        if filter_response is None or not self.blue_angel:
            return
        try:
            self.filter_code = int(filter_response[2:-1].split("\\n")[0])
        except ValueError:
            # an unreadable filter status must not stop the other values
            self.filter_status = FireplusFilterStatus.ERROR
        else:
            self.filter_status = _FILTER_STATUS_LOOKUP.get(self.filter_code, FireplusFilterStatus.ERROR)

    def __init_configuration_extras(self, configuration_values: list[str]) -> None:
        # Only known from web app 2.1.8 (firmware 2.4.6), which sends 11 values
        if len(configuration_values) > CONFIGURATION_EXTRAS:
            self.auto_update = configuration_values[2] == "1"
            self.online_support = configuration_values[5] == "1"
            self.web_app_version = configuration_values[8].strip()
            self.draught_warning = configuration_values[10] == "1"
        else:
            self.auto_update = None
            self.online_support = None
            self.web_app_version = None
            self.draught_warning = None

    def __init_control(self, panel_values: list[str]) -> None:
        # Names in the web app: PanelDa (0), BedienungVisu (1), FBda (14), FBAutomatik (15)
        panel_present = panel_values[0] == "1"
        remote_control = panel_values[14] == "1"
        remote_control_mode = int(panel_values[15])
        # stove with the Blue Angel label, its web app offers only two burn rates
        self.blue_angel = bool(int(panel_values[13]) & BLUE_ANGEL_FLAG)
        if remote_control and remote_control_mode == REMOTE_CONTROL_MANUAL:
            self.control_mode = FireplusControlMode.REMOTE_CONTROL
        elif remote_control and remote_control_mode == REMOTE_CONTROL_AUTOMATIC:
            self.control_mode = FireplusControlMode.REMOTE_CONTROL_AUTOMATIC
        elif remote_control_mode == ROOM_CONTROLLER:
            self.control_mode = FireplusControlMode.ROOM_CONTROLLER
        elif panel_present and not self.web_controls_shown:
            self.control_mode = FireplusControlMode.PANEL
        else:
            self.control_mode = FireplusControlMode.WEB

    @property
    def locked_settings(self) -> frozenset[str]:
        """Return the settings the web app does not allow to change right now."""
        if self.control_mode in (FireplusControlMode.REMOTE_CONTROL, FireplusControlMode.REMOTE_CONTROL_AUTOMATIC):
            return frozenset({"burn_rate", "brightness", "volume", "ember_burndown"})
        if self.control_mode in (FireplusControlMode.ROOM_CONTROLLER, FireplusControlMode.PANEL):
            return frozenset({"burn_rate"})
        return frozenset()

    def __init_version1(self, panel_values: list[str], configuration_values: list[str]) -> None:
        self.volume = None
        self.ember_burndown = panel_values[11] == "1"
        self.count = None
        self.led = panel_values[10] == "1"
        self.burn_rate = _get_burn_rate_v1(int(panel_values[2]), int(panel_values[3]))
        self.operating_time = None
        self.heating_progress = _percentage(int(panel_values[12]), int(configuration_values[6]))
        self.door_open = None
        self.weight = None
        self.target_temperature = None
        self.ethernet_link = None
        self.wifi_signal_strength = None

    def __init_version2(self, panel_values: list[str], configuration_values: list[str]) -> None:
        self.volume = int(panel_values[12])
        self.ember_burndown = panel_values[10] == "1"
        self.count = int(panel_values[16])
        self.__init_control(panel_values)
        self.led = None
        self.burn_rate = _get_burn_rate_v2(int(panel_values[2]), int(panel_values[3]))
        self.operating_time = int(configuration_values[7])
        self.heating_progress = _percentage(int(panel_values[11]), int(configuration_values[6]))
        self.door_open = None
        self.weight = None
        self.target_temperature = None
        self.ethernet_link = None
        self.wifi_signal_strength = None

    def __init_version2_4(self, panel_values: list[str], configuration_values: list[str]) -> None:
        self.__init_version2(panel_values, configuration_values)
        self.door_open = (panel_values[19]) == "auf"
        self.weight = float(panel_values[18]) / 100
        self.target_temperature = int(panel_values[17])
        network = int(panel_values[20])
        self.ethernet_link = network == ETHERNET_LINK
        self.wifi_signal_strength = network if network > 0 and network < ETHERNET_LINK else None


def _percentage(value: int, total: int) -> float:
    return value / total * 100 if total else 0.0


class FireplusControlMode(Enum):
    """Who controls the fire+, as shown by its web app."""

    WEB = auto()
    PANEL = auto()
    REMOTE_CONTROL = auto()
    REMOTE_CONTROL_AUTOMATIC = auto()
    ROOM_CONTROLLER = auto()


class FireplusUpdateResult(Enum):
    """Result of the last software update, as shown by the service page of the web app."""

    NOT_STARTED = auto()
    STARTED = auto()
    NO_UPDATES = auto()
    RUNNING = auto()
    SUCCESSFUL = auto()
    FAILED = auto()
    POSTPONED = auto()
    UNKNOWN = auto()


# Codes of php/UpdateErgebniss.php ("<code>, <message>")
_UPDATE_RESULT_LOOKUP = {
    0: FireplusUpdateResult.NOT_STARTED,
    1: FireplusUpdateResult.STARTED,
    2: FireplusUpdateResult.NO_UPDATES,
    3: FireplusUpdateResult.RUNNING,
    4: FireplusUpdateResult.SUCCESSFUL,
    5: FireplusUpdateResult.FAILED,
    6: FireplusUpdateResult.POSTPONED,
}


def _decode_text(response: str) -> str:
    """Decode a text answer of the fire+: a JSON string after a byte order mark."""
    text = response.lstrip("\ufeff").strip()
    try:
        value = json.loads(text)
    except ValueError:
        value = text.strip('"')
    return str(value).strip()


@dataclass(frozen=True)
class FireplusUpdateStatus:
    """Result of the last software update and the time of the weekly update search."""

    result: FireplusUpdateResult
    code: int | None
    message: str
    schedule: str

    @classmethod
    def parse(cls, result_response: str, schedule_response: str) -> FireplusUpdateStatus:
        """Parse the answers of UpdateErgebniss.php and easupdate.php."""
        code_text, _, message = _decode_text(result_response).partition(",")
        try:
            code: int | None = int(code_text)
        except ValueError:
            code = None
        return cls(
            result=_UPDATE_RESULT_LOOKUP.get(code, FireplusUpdateResult.UNKNOWN)
            if code is not None
            else FireplusUpdateResult.UNKNOWN,
            code=code,
            message=message.strip(),
            schedule=_decode_text(schedule_response),
        )


class FireplusFilterStatus(Enum):
    """Status of the OekoSolve particle filter of stoves with the Blue Angel label."""

    DRIVER_ERROR = auto()
    NOT_FOUND = auto()
    PRESENT = auto()
    INACTIVE = auto()
    ACTIVE = auto()
    CLEANING_REQUIRED = auto()
    ERROR = auto()


# Answers of php/oeko.php as shown by the web app, other values are shown as "Filter Fehler <code>"
_FILTER_STATUS_LOOKUP = {
    0: FireplusFilterStatus.DRIVER_ERROR,
    1: FireplusFilterStatus.NOT_FOUND,
    2: FireplusFilterStatus.PRESENT,
    3: FireplusFilterStatus.INACTIVE,
    4: FireplusFilterStatus.ACTIVE,
    5: FireplusFilterStatus.CLEANING_REQUIRED,
}

# Filter states the web app shows in red
FILTER_PROBLEMS = frozenset(
    {
        FireplusFilterStatus.DRIVER_ERROR,
        FireplusFilterStatus.NOT_FOUND,
        FireplusFilterStatus.CLEANING_REQUIRED,
        FireplusFilterStatus.ERROR,
    }
)


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


# Lookup table of values for "Betrieb" and "Leistung" to burn rate (API v2);
# like the web app, "Betrieb" 1 counts as the lowest stage of its "Leistung"
_DERIVED_BURN_RATE_LOOKUP_V2 = {value: key for key, value in _BURN_RATE_LOOKUP_V2.items()} | {(1, 4): 1, (1, 8): 4}


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
