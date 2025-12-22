"""Constants for drooff_fireplus."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "drooff_fireplus"

DEFAULT_HOST = "fire"

UPDATE_FAILED_MSG = "Unable to retrieve updated data from Drooff fire+ API"

CONF_FORCE_IPV4 = "force_ipv4"

CONF_FORCE_IPV4_DEFAULT = True

CONF_POLLING_INTERVAL = "polling_interval"

DEFAULT_POLLING_INTERVAL = 5

MIN_POLLING_INTERVAL = 5

MAX_POLLING_INTERVAL = 60
