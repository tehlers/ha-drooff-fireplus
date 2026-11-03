# Drooff fire+ Card

[← Back to the integration](../README.md)

A Lovelace dashboard card for the Home Assistant integration [Drooff fire+](https://github.com/tehlers/ha-drooff-fireplus). It shows an animated fire whose size follows the current combustion state, next to the values and controls of the fire+ combustion control.

**[Deutsche Anleitung](dashboard-card.de.md)**

![Overview](images/overview.png)

## Features

- **Realistic fire animation** (canvas particle system with flame tongues and sparks) in a combustion chamber lined with **upright white fire-clay plates**, side walls in perspective, soot marks and flickering firelight. Light or dark brick walls can be selected instead.
- **Split firewood**: 25 cm beech logs with bark, fibres, knots and growth rings. They char and glow while burning. The fire follows the chamber temperature and the operation status:
  - *Off*: cold logs, faint embers while the stove is still warm
  - *Heating up*: the flame grows with the heating progress
  - *Regular*: flame size according to the temperature
  - *Add wood / add wood now*: smaller flame, charred logs
  - *Ember preservation*: dark red, slowly breathing ember bed without flames
  - *Ember burndown*: bright glowing embers with small flames and sparks
- Door open: dashed, pulsing frame around the window
- Operation status as coloured badge, error message as banner
- Temperature with target and maximum, heating progress, air slider, chimney draught
- **Recommended wood load shown as logs** (stack of split logs, half a log is drawn smaller)
- **Optional: a picture of your stove** – the fire is then shown inside its window (default is the open fireplace)
- Burn rate (1–6 or 1–7) and ember burndown can be changed directly in the card (`controls: false` turns this off)
- Settings and diagnostics of the fire+: LED on/off, LED brightness and volume (with slider), Wi-Fi signal, Ethernet link, operating time
- **Automatic detection**: the card editor finds the fire+ device and all of its entities and preselects everything your device provides under “Show”. Unticking hides the value. The detected entities are listed under “Entities” and can be changed.
- **Chimney draught as gauge** (optional): scale −10 to 25 Pa, green normal range for the current burn rate (part load/stage 1: 6 Pa, full load/stage 6: 12 Pa, linear in between, ± 2 Pa), everything adjustable under “Advanced: draught”
- **Additional graphics** (each optional, off by default):
  - `temp_history` temperature history of the last hours with target line (from the HA recorder)
  - `timeline` burn timeline as coloured band with legend
  - `wood_usage` estimated wood usage per day (every heating up / adding wood counts as one load with the wood load recommended at that time, otherwise `wood_per_load`)
  - `heating_ring` glowing progress ring around the window while heating up
  - `air_flap` air slider as animated damper flap
  - `temp_ring` temperature as ring with target and maximum markers
- **Simulate fire**: button in the card editor that plays all phases once in the preview without touching the stove
- **Languages**: German, English, Dutch, French, Italian, Polish, Czech, Danish – automatically from the user language or fixed (`language`). Any other language can be added with your own language code and `translations`.
- Card version is shown at the bottom of the card editor
- The animation pauses while the card is not visible

## Installation

The card is part of the Drooff fire+ integration and is loaded automatically once the integration is installed. No resource has to be added and HACS does not need a separate entry.

Then edit a dashboard → *Add card* → **Drooff fire+ Card**, or in YAML:

```yaml
type: custom:drooff-fireplus-card
```

Everything else is detected automatically.

## Options

| Option | Default | Description |
| --- | --- | --- |
| `title` | device name | Heading |
| `language` | `auto` | `auto` (user language), `de`, `en`, `nl`, `fr`, `it`, `pl`, `cs`, `da` or any own code (e.g. `es`) |
| `translations` | – | Own texts that override the built-in ones; missing texts fall back to English (see [template](examples/translations-template.yaml)) |
| `device` | first fire+ device | Device id, only needed with several stoves |
| `min_temperature` | `80` | Chamber temperature below which no flame is shown (°C) |
| `max_temperature` | `600` | Temperature for the full flame (°C) |
| `log_weight` | `0.9` | Weight of one log in kg (converts the wood load into logs) |
| `wall` | `chamotte` | Chamber background: `chamotte` (upright fire-clay plates), `bricks_light`, `bricks_dark` |
| `stove_image` | – | Picture of the stove (file picker in the editor, or a URL like `/local/stove.png`). Without it the open fireplace is shown |
| `stove_window` | `{left: 20, top: 20, width: 60, height: 40}` | Position of the window in the picture, in percent of width/height |
| `stove_window_radius` | `4` | Corner radius of the window in px |
| `stove_window_debug` | `false` | Shows the window as red frame for alignment |
| `draught_display` | `tile` | Chimney draught as `tile` or `gauge` |
| `draught_min` / `draught_max` | `-10` / `25` | Gauge scale in Pa |
| `draught_part_load` / `draught_part_stage` | `6` / `1` | Target draught in Pa at part load and its burn rate stage |
| `draught_full_load` / `draught_full_stage` | `12` / `6` | Target draught in Pa at full load and its burn rate stage |
| `draught_tolerance` | `2` | Width of the green normal range ± Pa around the target |
| `graphics` | `[]` | Additional graphics: `temp_history`, `timeline`, `wood_usage`, `heating_ring`, `air_flap`, `temp_ring` |
| `history_hours` | `6` | Time span of temperature history and timeline in hours |
| `wood_days` | `7` | Number of days for the wood usage |
| `wood_per_load` | `2` | kg per load if there is no wood load sensor |
| `controls` | `true` | Burn rate, ember burndown, LED, brightness and volume can be changed in the card |
| `layout` | `auto` | `auto` (narrow = stacked), `horizontal`, `vertical` |
| `hide` | `[brightness, volume, wifi, ethernet]` | Hidden elements, see below |
| `entities` | automatic | Assign entities manually, e.g. `temperature: sensor.stove_temperature` |
| `flame_intensity` | – | Fixed flame size (0–1), e.g. for testing |

Without `hide`, LED brightness, volume, Wi-Fi and Ethernet are hidden and everything else is shown; `hide: []` shows everything. Values for `hide`: `flame`, `name`, `status`, `temperature`, `target_temperature`, `max_temperature`, `heating_progress`, `burn_rate`, `air_slider`, `draught`, `wood_load`, `wood_logs` (only the log graphic), `door`, `ember_burndown`, `error`, `operating_time`, `led`, `brightness`, `volume`, `wifi`, `ethernet`.

Keys for `entities`: `operation_status`, `temperature`, `target_temperature`, `heating_progress`, `air_slider_position`, `draught`, `weight`, `error_message`, `operating_time`, `burn_rate`, `ember_burndown`, `error`, `door_open`, `led`, `brightness`, `volume`, `wifi_signal_strength`, `ethernet_link`.

Values your stove does not provide (e.g. wood load on older devices, heating progress outside of heating up) are hidden automatically.

A complete dashboard example is in [examples/dashboard.yaml](examples/dashboard.yaml).

## Picture of your stove

![Stove picture](images/stove-picture.png)

1. Edit the card, click **Choose picture …** in the section **Stove picture** and select a front photo of your stove (white background works best, e.g. the product picture of the manufacturer).
2. The card scales the picture down, makes a white background transparent, crops it to the stove and **detects the window automatically**. The red marker in the preview shows where the fire will appear.
3. Fine-tune under **Window** (left/top/width/height in percent, corner radius) if necessary.
4. **Remove** switches back to the open fireplace.

The picture is stored in the card configuration (typically 10–60 KB), nothing has to be copied to `/config/www`. A URL works as well:

```yaml
stove_image: /local/stove.png
stove_window: { left: 12, top: 37, width: 70, height: 27 }
stove_window_radius: 6
```

Please only use pictures you are allowed to use; product photos are usually copyrighted by the manufacturer.

## Chimney draught gauge

![Draught gauge](images/draught-gauge.png)

## Additional graphics

![Graphics](images/graphics.png)

`temp_history`, `timeline` and `wood_usage` read the Home Assistant history (recorder) and are refreshed every 5 minutes. The wood usage is an estimate.

## Own language

Type your own language code under **Language** in the card editor (e.g. `es`) and enter the texts under **Advanced: language / custom translation**. In YAML:

```yaml
type: custom:drooff-fireplus-card
language: es
translations:
  temperature: Cámara de combustión
  burn_rate: Potencia
  status:
    REGULAR: Funcionamiento normal
    WOOD_REQUIRED: Añadir leña
```

[examples/translations-template.yaml](examples/translations-template.yaml) lists all keys with the English texts, [examples/translations-example-de.yaml](examples/translations-example-de.yaml) shows a complete translation using German as example. `translations` also works with built-in languages to change single texts. Pull requests with new languages are welcome.

## Disclaimer

This card is neither supported by nor affiliated with Drooff. Drooff and fire+ are trademarks of their respective owner.

## License

See [LICENSE](../LICENSE).
