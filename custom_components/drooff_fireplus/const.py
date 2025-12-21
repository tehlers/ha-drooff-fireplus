"""Constants for drooff_fireplus."""

import socket
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "drooff_fireplus"

DEFAULT_HOST = "fire"

UPDATE_FAILED_MSG = "Unable to retrieve updated data from Drooff fire+ API"

CONF_IP_VERSION = "ip_version"

CONF_IP_VERSION_DEFAULT = socket.AF_INET

CONF_POLLING_INTERVAL = "polling_interval"

DEFAULT_POLLING_INTERVAL = 10

MIN_POLLING_INTERVAL = 5

MAX_POLLING_INTERVAL = 60
