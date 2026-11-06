# Blueprint „Drooff fire+: Holz nachlegen / Add wood“

Die Integration installiert den Blueprint nach dem Start von Home Assistant nach `config/blueprints/automation/drooff_fireplus/wood_required_notification.yaml` und aktualisiert ihn mit jeder neuen Version. Ist eine Automation mit einer älteren Version des Blueprints aktiv, lädt die Integration die Automationen danach neu.

## Einrichten

1. *Einstellungen*, *Automationen & Szenen*, *Blueprints* öffnen.
2. **Drooff fire+: Holz nachlegen / Add wood** wählen.
3. Bei **Sprache** Deutsch oder Englisch wählen. Die Sprache bestimmt die Standardtexte (Titel, „Bitte Holz nachlegen.“, „Dringend Holz nachlegen!“). Eigene Texte ersetzen sie.
4. Bei **Betriebsstatus** den Sensor „Betriebsstatus“ des fire+ eintragen.
5. Optional bei **Empfohlene Holzauflage** den gleichnamigen Sensor eintragen. Dann wird die Menge in kg an die Nachricht angehängt, zum Beispiel „Bitte Holz nachlegen. (1.5 kg)“.
6. Im Bereich **Aktion bei Holz nachlegen** die gewünschten Kanäle ausfüllen und speichern.

## Sprache

Die Beschriftungen im Blueprint sind zweisprachig (Deutsch / Englisch), weil Home Assistant Blueprints nicht übersetzen kann. Die Auswahl **Sprache** schaltet die Standardtexte der Nachrichten um.

## Kanäle

Jeder Kanal ist optional. Leere Kanäle tun nichts. Jeder Kanal hat eine eigene **Verzögerung**. Er meldet sich erst, wenn der fire+ so lange ununterbrochen „Holz nachlegen“ anzeigt. Wird vorher nachgelegt, kommt nichts.

| Kanal | Eingaben | Aufruf |
|---|---|---|
| Nachricht | Aktionen, vorbelegt mit einer Benachrichtigung in Home Assistant (`notify.persistent_notification`) | wie eingetragen |
| Echo | Geräte von *Alexa Media Player* (HACS) mit Art „Ansage“ oder „TTS“; Notify-Entitäten von *Alexa Devices* (z. B. `notify.kueche_announce`); eigener Ansagetext | `notify.alexa_media`; `notify.send_message` |
| Weitere Aktionen | Beliebige Aktionen, die Variablen `title` und `text` enthalten Titel und Nachricht | wie eingetragen |

### Nachricht per Pushover (oder Handy-App, Telegram, …)

Unter **Nachricht: Aktionen** im Aktions-Editor:

1. Die vorbelegte Aktion öffnen, über das Drei-Punkte-Menü *Aktion ändern* bzw. eine neue Aktion hinzufügen und **Benachrichtigungen: Send a notification via pushover** wählen (bei der Handy-App *notify.mobile_app_…*).
2. **Nachricht:** `{{ text }}` eintragen, **Titel:** `{{ title }}`.
3. Optional unter **Daten** Pushover-Felder setzen, zum Beispiel:
   ```yaml
   priority: 1
   sound: siren
   ```
4. Die vorbelegte Home-Assistant-Benachrichtigung löschen, wenn sie nicht mehr gebraucht wird.

In YAML sieht das so aus:
```yaml
- action: notify.pushover
  data:
    title: "{{ title }}"
    message: "{{ text }}"
    data:
      priority: 1
      sound: siren
```
Mehrere Empfänger sind einfach mehrere Aktionen. Ein leerer Kanal (alle Aktionen gelöscht) sendet nichts.

## Dringend Holz nachlegen

Der Bereich **Aktion bei Dringend Holz nachlegen** ist zugeklappt. Er hat dieselben Kanäle und Texte wie „Holz nachlegen“ und gilt erst, wenn dort **Eigene Aktionen bei „Dringend“ verwenden / Use own actions when urgent** eingeschaltet ist. Solange der Schalter aus ist, löst auch „Dringend Holz nachlegen“ die Aktionen für „Holz nachlegen“ aus, mit deren Verzögerung, aber mit dem Standardtext für „Dringend“.

Wechselt der Status von „Holz nachlegen“ zu „Dringend“, werden noch ausstehende Erinnerungen für „Holz nachlegen“ verworfen und die Kanäle für „Dringend“ starten mit ihren eigenen Verzögerungen.

## Anpassen

Änderungen an der installierten Datei werden beim nächsten Update überschrieben. Für eigene Anpassungen die Datei im selben Ordner unter einem anderen Namen speichern.
