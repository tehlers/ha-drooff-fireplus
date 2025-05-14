# Drooff fire+ integration for Home Assistant

A custom integration for [Home Assistant](https://www.home-assistant.io/) for the [Drooff fire+](https://www.drooff-kaminofen.de/en/nature/electronic-combustion-control-fire/) combustion control system.

![Screenshot of dashboard showing fire+ entities](https://github.com/user-attachments/assets/b5256699-66cc-46d9-af58-e03d29749a92)

## Installation

### HACS Installation

1. Ensure that [HACS](https://hacs.xyz) is installed.
2. Go to the HACS settings and add https://github.com/tehlers/ha-drooff-fireplus as a custom repository.
3. Search for "Drooff fire+" in HACS and install it.
4. Restart Home Assistant.

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tehlers&repository=ha-drooff-fireplus&category=integration)

### Manual Installation

1. Copy the directory `custom_components/drooff_fireplus` to `custom_components` in the `config` directory of your Home Assistant.
2. Restart Home Assistant.

## Configuration

1. Go to the Home Assistant dashboard.
2. Navigate to `Configuration` > `Devices & Services` > `Add Integration`.
3. Search for "Drooff fire+" and select it.
4. You will be prompted to enter the hostname used by your Drooff fire+ combustion control system. In the default configuration, this is "fire".

## Disclaimer

This integration is neither supported nor affiliated with Drooff. It is intended as a supplement to the official fire+ webapp and not a full replacement.
