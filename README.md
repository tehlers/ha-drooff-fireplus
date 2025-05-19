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
4. You will be prompted to enter the hostname used by your Drooff fire+ web application. In the default configuration, this is "fire".

## Entities

### Controls

| Name             | Type   | Description                                              |
| ---------------- | ------ | -------------------------------------------------------- |
| `Burn rate`      | Number | Select burn rate in six stages between "Eco" and "Power" |
| `Ember burndown` | Switch | Toggle between "Ember preservation" and "Ember burndown" |

### Sensors

| Name                  | Type   | Description                                                   |
| --------------------- | ------ | ------------------------------------------------------------- |
| `Air slider position` | Sensor | Position of the air slider in percent                         |
| `Draught`             | Sensor | Chimney draught in Pa                                         |
| `Heating progress`    | Sensor | Heating progress in percent (only available while `HEATING`) |
| `Operation status`    | Sensor | Operation status of the fireplace. Possible values are:<br>- `STANDBY`<br>- `REGULAR`<br>- `HEATING`<br>- `WOOD_REQUIRED`<br>- `WOOD_URGENTLY_REQUIRED`<br>- `EMBER_PRESERVATION`<br>- `EMBER_BURNDOWN`<br>- `ERROR`<br>- `UNKNOWN` |
| `Temperature`         | Sensor | Temperature inside the combustion chamber in °C               |

### Configuration

| Name         | Type   | Description                              |
| ------------ | ------ | ---------------------------------------- |
| `Brightness` | Number | Brightness of the LED strip in percent   |
| `Volume`     | Number | Volume of the acoustic signal in percent |

### Diagnostic

| Name             | Type          | Description                                |
| ---------------- | ------------- | ------------------------------------------ |
| `Error`          | Binary Sensor | Active when an error has been detected     |
| `Error message`  | Sensor        | Description of the detected error. Possible values are:<br>- "No error"<br>- "Temperature sensor defective"<br>- "Pressure measurement defective"<br>- "Air slider defective"<br>- "Service mode enabled"<br>- "Chimney draught too low"<br>- "Air slider stuck"<br>- "No chimney draught"<br>- "Wrong motor direction"<br>- "Unknown error"<br><br>**Always consult the official fire+ web application in the event of an error!** |
| `Operating time` | Sensor        | Total operating time of the fireplace in s |

## Disclaimer

This integration is neither supported nor affiliated with Drooff. It is intended as a supplement to the official fire+ webapp and not a full replacement.
