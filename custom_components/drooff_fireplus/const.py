"""Constants for drooff_fireplus."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "drooff_fireplus"

DEFAULT_HOST = "fire"

UPDATE_FAILED_MSG = "Unable to retrieve updated data from Drooff fire+ API"
