# Blueprint "Drooff fire+: Holz nachlegen / Add wood"

Once Home Assistant has started, the integration installs the blueprint to `config/blueprints/automation/drooff_fireplus/wood_required_notification.yaml` and updates it with every new version. If the installed file changed, automations are reloaded so they use the new version.

## Setup

1. Open *Settings*, *Automations & scenes*, *Blueprints*.
2. Choose **Drooff fire+: Holz nachlegen / Add wood**.
3. Choose German or English as **Sprache / Language**. It selects the default texts (title, "Please add wood.", "Add wood now!"); own texts replace them.
4. Select the *operation status* sensor of the fire+ as **Betriebsstatus / Operation status**.
5. Optionally select the *recommended wood load* sensor as **Empfohlene Holzauflage / Recommended wood load**, the amount in kg is then appended to the message.
6. Fill in the channels in the section **Aktion bei Holz nachlegen / Action when wood is required** and save.

## Language

The labels of the blueprint are bilingual (German / English), because Home Assistant can not translate blueprints. **Sprache / Language** switches the default texts of the messages.

## Channels

Every channel is optional and has its own **delay** (*Verzögerung*). It only fires if the fire+ still asks for wood after the delay, so nothing is sent once the wood has been added.

| Channel | Inputs | Action |
|---|---|---|
| Message (*Nachricht*) | actions, preset with a Home Assistant notification (`notify.persistent_notification`) | as entered |
| Echo | devices of *Alexa Media Player* (HACS) with type announce or TTS; notify entities of *Alexa Devices* (e.g. `notify.kitchen_announce`); own announcement text | `notify.alexa_media`; `notify.send_message` |
| Other actions (*Weitere Aktionen*) | any actions, the variables `title` and `text` hold title and message | as entered |

### Message via Pushover (or mobile app, Telegram, …)

In **Message: actions**, change the preset action or add one, choose **Notifications: Send a notification via pushover** (or *notify.mobile_app_…*), enter `{{ text }}` as message and `{{ title }}` as title, and optionally set Pushover fields under data. In YAML:
```yaml
- action: notify.pushover
  data:
    title: "{{ title }}"
    message: "{{ text }}"
    data:
      priority: 1
      sound: siren
```
Several recipients are several actions. An empty channel sends nothing.

## Wood urgently required

The section **Aktion bei Dringend Holz nachlegen / Action when wood is urgently required** is collapsed. It has the same channels and texts and is only used once **Use own actions when urgent** is switched on. Until then, *wood urgently required* runs the actions for *wood required*, with their delays but the urgent default text.

When the status changes from *wood required* to *urgently required*, pending reminders for *wood required* are dropped and the urgent channels start with their own delays.

## Customising

Changes to the installed file are overwritten on the next update. Save a copy under another name in the same folder to customise it.
