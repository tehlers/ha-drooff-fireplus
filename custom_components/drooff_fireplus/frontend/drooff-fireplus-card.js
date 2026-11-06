/*
 * Drooff fire+ Card for Home Assistant
 * Custom Lovelace card for the integration https://github.com/tehlers/ha-drooff-fireplus
 *
 * Shows an animated flame whose size follows the current combustion state
 * next to the values of the fire+ combustion control. Every value can be hidden.
 */

const CARD_VERSION = "1.0.1";
const DOMAIN = "drooff_fireplus";

/* translation_key -> entity domain, plus entity_id suffixes as fallback */
const KEYS = {
  operation_status: { domain: "sensor", suffix: ["operation_status", "betriebsstatus"] },
  temperature: { domain: "sensor", suffix: ["temperature", "temperatur"] },
  target_temperature: { domain: "sensor", suffix: ["target_temperature", "zieltemperatur"] },
  heating_progress: { domain: "sensor", suffix: ["heating_progress", "anheizenfortschritt"] },
  air_slider_position: { domain: "sensor", suffix: ["air_slider_position", "luftschieberposition"] },
  draught: { domain: "sensor", suffix: ["draught", "feinzug"] },
  weight: { domain: "sensor", suffix: ["recommended_wood_load", "empfohlene_holzauflage", "weight"] },
  error_message: { domain: "sensor", suffix: ["error_message", "fehlermeldung"] },
  operating_time: { domain: "sensor", suffix: ["operating_time", "betriebszeit"] },
  burn_rate: { domain: "number", suffix: ["burn_rate", "brennleistung"] },
  ember_burndown: { domain: "switch", suffix: ["ember_burndown", "glutabbrand"] },
  error: { domain: "binary_sensor", suffix: ["error", "fehler"] },
  door_open: { domain: "binary_sensor", suffix: ["door", "door_open", "tur", "tuer"] },
  led: { domain: "switch", suffix: ["led"] },
  brightness: { domain: "number", suffix: ["brightness", "helligkeit"] },
  volume: { domain: "number", suffix: ["volume", "lautstarke", "lautstaerke"] },
  wifi_signal_strength: { domain: "sensor", suffix: ["wifi_signal_strength", "wlan_signalstarke"] },
  ethernet_link: { domain: "binary_sensor", suffix: ["ethernet_link", "ethernet_verbindung"] },
};

/* Values that can be hidden via `hide:` */
const HIDEABLE = [
  "flame",
  "name",
  "status",
  "temperature",
  "target_temperature",
  "max_temperature",
  "heating_progress",
  "burn_rate",
  "air_slider",
  "draught",
  "wood_load",
  "wood_logs",
  "door",
  "ember_burndown",
  "error",
  "operating_time",
  "led",
  "brightness",
  "volume",
  "wifi",
  "ethernet",
];

/* which entity an element needs (elements without entry are always available) */
const NEEDS = {
  status: "operation_status",
  temperature: "temperature",
  target_temperature: "target_temperature",
  max_temperature: "temperature",
  heating_progress: "heating_progress",
  burn_rate: "burn_rate",
  air_slider: "air_slider_position",
  draught: "draught",
  wood_load: "weight",
  wood_logs: "weight",
  door: "door_open",
  ember_burndown: "ember_burndown",
  error: "error",
  operating_time: "operating_time",
  led: "led",
  brightness: "brightness",
  volume: "volume",
  wifi: "wifi_signal_strength",
  ethernet: "ethernet_link",
};

/* hidden unless the configuration says otherwise */
const DEFAULT_HIDE = ["brightness", "volume", "wifi", "ethernet"];
const hideList = (cfg) => (Array.isArray(cfg.hide) ? cfg.hide : DEFAULT_HIDE);

const GRAPHICS = ["temp_history", "timeline", "wood_usage", "heating_ring", "air_flap", "temp_ring"];

const DEFAULTS = {
  history_hours: 6,
  wood_days: 7,
  wood_per_load: 2,
  draught_display: "tile",
  draught_min: -30,
  draught_max: 10,
  draught_optimal_from: -12,
  draught_optimal_to: -20,
  language: "auto", min_temperature: 80, max_temperature: 600, log_weight: 0.9, controls: true, layout: "auto", wall: "chamotte" };

/* find the entities of the integration */
const resolveFireplus = (hass, cfg = {}) => {
  const out = {};
  const reg = hass.entities || {};
  let device = cfg.device;

  const candidates = Object.values(reg).filter((e) => e.platform === DOMAIN);
  if (!device && candidates.length) {
    const devices = [...new Set(candidates.map((e) => e.device_id).filter(Boolean))];
    if (devices.length) device = devices[0];
  }
  const own = candidates.filter((e) => !device || e.device_id === device);

  for (const [key, def] of Object.entries(KEYS)) {
    const hit = own.find((e) => e.translation_key === key && e.entity_id.startsWith(def.domain + "."));
    if (hit) out[key] = hit.entity_id;
  }

  /* fallback: entity_id suffixes (older HA without translation_key in hass.entities) */
  const prefix = cfg.entity_prefix;
  for (const [key, def] of Object.entries(KEYS)) {
    if (out[key]) continue;
    const hit = Object.keys(hass.states).find((id) => {
      if (!id.startsWith(def.domain + ".")) return false;
      const obj = id.split(".")[1];
      if (prefix) {
        if (!obj.startsWith(prefix)) return false;
      } else if (candidates.length) {
        if (!reg[id] || reg[id].platform !== DOMAIN || (device && reg[id].device_id !== device)) return false;
      }
      return def.suffix.some((sfx) => obj.endsWith("_" + sfx));
    });
    if (hit) out[key] = hit;
  }
  return { detected: { ...out }, entities: { ...out, ...(cfg.entities || {}) }, device };
};

const I18N = {
  de: {
    title: "Kaminofen",
    status: {
      STANDBY: "Aus",
      REGULAR: "Regelbetrieb",
      HEATING: "Anheizen",
      WOOD_REQUIRED: "Holz nachlegen",
      WOOD_URGENTLY_REQUIRED: "Dringend Holz nachlegen",
      EMBER_PRESERVATION: "Gluterhaltung",
      EMBER_BURNDOWN: "Glutabbrand",
      ERROR: "Fehler",
      UNKNOWN: "Unbekannt",
    },
    temperature: "Brennraum",
    target: "Ziel",
    max: "Max",
    heating_progress: "Anheizen",
    burn_rate: "Brennleistung",
    eco: "Eco",
    power: "Power",
    air_slider: "Luftschieber",
    draught: "Kaminzug",
    wood_load: "Empfohlene Holzauflage",
    log: "Scheit",
    logs: "Scheite",
    door: "Tür",
    open: "offen",
    closed: "geschlossen",
    ember: "Glut",
    ember_on: "Abbrand",
    ember_off: "Erhalten",
    operating_time: "Betriebszeit",
    brightness: "Helligkeit",
    volume: "Lautstärke",
    wifi: "WLAN",
    on: "an",
    off: "aus",
    connected: "verbunden",
    disconnected: "getrennt",
    hours: "h",
    simulation: "Simulation",
    temp_history: "Temperaturverlauf",
    timeline: "Abbrand-Zeitleiste",
    wood_usage: "Holzverbrauch (geschätzt)",
    now: "jetzt",
    no_history: "Noch keine Verlaufsdaten.",
    draught_target: "Optimal",
    stage: "Stufe",
    draught_ok: "optimal",
    draught_low: "schwacher Zug",
    draught_high: "OK (starker Zug)",
    draught_negative: "Überdruck",
    error: "Fehler",
    not_found: "Keine Drooff fire+ Entitäten gefunden. Bitte `device` oder `entities` konfigurieren.",
    editor: {
      graphics: "Zusätzliche Grafiken",
      history_hours: "Verlauf/Zeitleiste: Stunden",
      wood_days: "Holzverbrauch: Tage",
      wood_per_load: "Holz pro Ladung ohne Sensor (kg)",
      title: "Titel (leer = Gerätename)",
      device: "Gerät",
      min_temperature: "Temperatur ohne Flamme (°C)",
      max_temperature: "Temperatur für volle Flamme (°C)",
      controls: "Bedienung erlauben (Brennleistung, Glutabbrand)",
      log_weight: "Gewicht eines Holzscheits (kg)",
      layout: "Layout",
      language: "Sprache",
      draught_display: "Kaminzug-Anzeige",
      advanced: "Erweitert: Kaminzug",
      draught_min: "Skala von (Pa)",
      draught_max: "Skala bis (Pa)",
      draught_optimal_from: "Optimal ab (Pa)",
      draught_optimal_to: "Optimal bis (Pa)",
      lang_auto: "Automatisch (Benutzersprache)",
      draught_tile: "Kachel",
      draught_gauge: "Zeigerinstrument (Gauge)",
      layout_horizontal: "Nebeneinander",
      layout_vertical: "Untereinander",
      advanced_language: "Erweitert: Sprache / eigene Übersetzung",
      translations: "Eigene Übersetzungen (überschreiben einzelne Texte, siehe README)",
      sim_start: "🔥 Feuer simulieren",
      sim_stop: "Simulation beenden",
      sim_hint: "Spielt in der Vorschau einmal alle Phasen durch: Anheizen, Regelbetrieb, Holz nachlegen, Glutabbrand, Gluterhaltung.",
      wall: "Brennraum-Hintergrund",
      show: "Anzeigen (erkannte fire+ Werte)",
      stove_picture: "Ofenbild (optional)",
      stove_pick: "Bild auswählen …",
      stove_model: "Ofenmodell (Drooff)",
      stove_model_none: "– kein Modell –",
      stove_model_info: "{kw} kW · Mindestförderdruck {pa} Pa. Optimaler Zug −{pa} … −{max} Pa wurde übernommen (änderbar unter „Erweitert: Kaminzug“).",
      stove_model_link: "Produktseite bei Drooff öffnen",
      stove_model_steps: "So kommt das Ofenbild in die Karte: 1. Produktseite öffnen und die gewünschte Ausführung wählen. 2. Das freigestellte Produktbild (Ofen ohne Hintergrund) mit Rechtsklick → „Bild speichern unter …“ auf deinem Gerät speichern. 3. Hier „Bild auswählen …“ klicken und die Datei wählen. Die Karte stellt das Bild frei und erkennt die Scheibe automatisch.",
      stove_model_copyright: "Die Produktbilder sind urheberrechtlich geschützt (© Drooff). Deshalb lädt die Karte sie nicht selbst herunter und liefert sie nicht mit. Bitte nur privat im eigenen Dashboard verwenden.",
      stove_remove: "Entfernen",
      stove_loading: "Bild wird verarbeitet …",
      stove_error: "Das Bild konnte nicht gelesen werden.",
      stove_none: "Ohne Bild wird die Feuerstelle gezeigt. Wähle ein Foto deines Ofens (frontal, gern mit weißem Hintergrund) – das Sichtfenster wird automatisch erkannt.",
      stove_hint: "Rot markiert: hier erscheint das Feuer. Bei Bedarf unter „Sichtfenster“ feinjustieren.",
      stove_not_found: "Kein Sichtfenster erkannt – bitte unter „Sichtfenster“ einstellen.",
      stove_window: "Sichtfenster (Prozent des Bildes)",
      left: "Links",
      top: "Oben",
      width: "Breite",
      height: "Höhe",
      stove_window_radius: "Eckenradius",
      stove_window_debug: "Sichtfenster zum Ausrichten markieren",
      entities: "Entitäten (automatisch erkannt)",
      hide: "Ausblenden",
    },
    hide_labels: {
      flame: "Flammenanimation",
      name: "Titel",
      status: "Betriebsstatus",
      temperature: "Temperatur",
      target_temperature: "Zieltemperatur",
      max_temperature: "Maximaltemperatur",
      heating_progress: "Anheizfortschritt",
      burn_rate: "Brennleistung",
      air_slider: "Luftschieber",
      draught: "Kaminzug",
      wood_load: "Empfohlene Holzauflage",
      wood_logs: "Holzscheite-Grafik",
      door: "Tür",
      ember_burndown: "Glutabbrand",
      error: "Fehlermeldung",
      operating_time: "Betriebszeit",
      led: "LED",
      brightness: "LED-Helligkeit",
      volume: "Lautstärke",
      wifi: "WLAN-Signal",
      ethernet: "LAN-Verbindung",
    },
    graphics_labels: {temp_history: "Temperaturverlauf", timeline: "Abbrand-Zeitleiste", wood_usage: "Holzverbrauch pro Tag", heating_ring: "Anheizfortschritt als Ring", air_flap: "Luftschieber als Klappe", temp_ring: "Temperatur als Ring" },
    walls: { chamotte: "Schamotteplatten (hochkant)", bricks_light: "Mauer hell", bricks_dark: "Mauer dunkel" },
  },
  en: {
    title: "Fireplace",
    status: {
      STANDBY: "Off",
      REGULAR: "Regular",
      HEATING: "Heating up",
      WOOD_REQUIRED: "Add wood",
      WOOD_URGENTLY_REQUIRED: "Add wood now",
      EMBER_PRESERVATION: "Ember preservation",
      EMBER_BURNDOWN: "Ember burndown",
      ERROR: "Error",
      UNKNOWN: "Unknown",
    },
    temperature: "Chamber",
    target: "Target",
    max: "Max",
    heating_progress: "Heating up",
    burn_rate: "Burn rate",
    eco: "Eco",
    power: "Power",
    air_slider: "Air slider",
    draught: "Draught",
    wood_load: "Recommended wood load",
    log: "log",
    logs: "logs",
    door: "Door",
    open: "open",
    closed: "closed",
    ember: "Ember",
    ember_on: "Burndown",
    ember_off: "Preserve",
    operating_time: "Operating time",
    brightness: "Brightness",
    volume: "Volume",
    wifi: "Wi-Fi",
    on: "on",
    off: "off",
    connected: "connected",
    disconnected: "disconnected",
    hours: "h",
    simulation: "Simulation",
    temp_history: "Temperature history",
    timeline: "Burn timeline",
    wood_usage: "Wood usage (estimated)",
    now: "now",
    no_history: "No history data yet.",
    draught_target: "Optimal",
    stage: "stage",
    draught_ok: "optimal",
    draught_low: "weak draught",
    draught_high: "OK (strong draught)",
    draught_negative: "overpressure",
    error: "Error",
    not_found: "No Drooff fire+ entities found. Please configure `device` or `entities`.",
    editor: {
      graphics: "Additional graphics",
      history_hours: "History/timeline: hours",
      wood_days: "Wood usage: days",
      wood_per_load: "Wood per load without sensor (kg)",
      title: "Title (empty = device name)",
      device: "Device",
      min_temperature: "Temperature without flame (°C)",
      max_temperature: "Temperature for full flame (°C)",
      controls: "Allow controls (burn rate, ember burndown)",
      log_weight: "Weight of one log (kg)",
      layout: "Layout",
      language: "Language",
      draught_display: "Draught display",
      advanced: "Advanced: draught",
      draught_min: "Scale from (Pa)",
      draught_max: "Scale to (Pa)",
      draught_optimal_from: "Optimal from (Pa)",
      draught_optimal_to: "Optimal to (Pa)",
      lang_auto: "Automatic (user language)",
      draught_tile: "Tile",
      draught_gauge: "Gauge",
      layout_horizontal: "Side by side",
      layout_vertical: "Stacked",
      advanced_language: "Advanced: language / custom translation",
      translations: "Custom translations (override single texts, see README)",
      sim_start: "🔥 Simulate fire",
      sim_stop: "Stop simulation",
      sim_hint: "Plays all phases once in the preview: heating, regular, add wood, ember burndown, ember preservation.",
      wall: "Chamber background",
      show: "Show (detected fire+ values)",
      stove_picture: "Stove picture (optional)",
      stove_pick: "Choose picture …",
      stove_model: "Stove model (Drooff)",
      stove_model_none: "– no model –",
      stove_model_info: "{kw} kW · minimum draught {pa} Pa. Optimal draught −{pa} … −{max} Pa was applied (can be changed under “Advanced: draught”).",
      stove_model_link: "Open product page at Drooff",
      stove_model_steps: "How to get the stove picture into the card: 1. Open the product page and choose the variant you have. 2. Right-click the cut-out product picture (stove without background) → “Save image as …” and save it on your device. 3. Click “Choose picture …” here and select the file. The card removes the background and detects the window automatically.",
      stove_model_copyright: "The product pictures are protected by copyright (© Drooff). That is why the card neither downloads nor ships them. Please use them only privately in your own dashboard.",
      stove_remove: "Remove",
      stove_loading: "Processing picture …",
      stove_error: "The picture could not be read.",
      stove_none: "Without a picture the open fireplace is shown. Choose a front photo of your stove (white background works best) – the window is detected automatically.",
      stove_hint: "Red area: this is where the fire appears. Fine-tune under “Window” if needed.",
      stove_not_found: "No window detected – please set it under “Window”.",
      stove_window: "Window (percent of the picture)",
      left: "Left",
      top: "Top",
      width: "Width",
      height: "Height",
      stove_window_radius: "Corner radius",
      stove_window_debug: "Mark the window for alignment",
      entities: "Entities (detected automatically)",
      hide: "Hide",
    },
    hide_labels: {
      flame: "Flame animation",
      name: "Title",
      status: "Operation status",
      temperature: "Temperature",
      target_temperature: "Target temperature",
      max_temperature: "Max temperature",
      heating_progress: "Heating progress",
      burn_rate: "Burn rate",
      air_slider: "Air slider",
      draught: "Draught",
      wood_load: "Recommended wood load",
      wood_logs: "Wood log graphic",
      door: "Door",
      ember_burndown: "Ember burndown",
      error: "Error message",
      operating_time: "Operating time",
      led: "LED",
      brightness: "LED brightness",
      volume: "Volume",
      wifi: "Wi-Fi signal",
      ethernet: "Ethernet link",
    },
    graphics_labels: {temp_history: "Temperature history", timeline: "Burn timeline", wood_usage: "Wood usage per day", heating_ring: "Heating progress as ring", air_flap: "Air slider as flap", temp_ring: "Temperature as ring" },
    walls: { chamotte: "Fire-clay plates (upright)", bricks_light: "Light brick wall", bricks_dark: "Dark brick wall" },
  },
  nl: {
    title: "Kachel",
    status: {
      STANDBY: "Uit",
      REGULAR: "Normaal bedrijf",
      HEATING: "Opstoken",
      WOOD_REQUIRED: "Hout bijvullen",
      WOOD_URGENTLY_REQUIRED: "Dringend hout bijvullen",
      EMBER_PRESERVATION: "Gloed behouden",
      EMBER_BURNDOWN: "Gloed uitbranden",
      ERROR: "Fout",
      UNKNOWN: "Onbekend",
    },
    temperature: "Verbrandingskamer",
    target: "Doel",
    max: "Max",
    heating_progress: "Opstoken",
    burn_rate: "Brandvermogen",
    air_slider: "Luchtschuif",
    draught: "Schoorsteentrek",
    wood_load: "Aanbevolen houtlading",
    log: "blok",
    logs: "blokken",
    door: "Deur",
    open: "open",
    closed: "gesloten",
    ember: "Gloed",
    ember_on: "Uitbranden",
    ember_off: "Behouden",
    operating_time: "Bedrijfstijd",
    brightness: "Helderheid",
    volume: "Volume",
    wifi: "Wifi",
    on: "aan",
    off: "uit",
    connected: "verbonden",
    disconnected: "niet verbonden",
    hours: "u",
    simulation: "Simulatie",
    temp_history: "Temperatuurverloop",
    timeline: "Tijdlijn verbranding",
    wood_usage: "Houtverbruik (geschat)",
    now: "nu",
    no_history: "Nog geen historische gegevens.",
    draught_target: "Optimaal",
    stage: "stand",
    draught_ok: "optimaal",
    draught_low: "zwakke trek",
    draught_high: "OK (sterke trek)",
    draught_negative: "overdruk",
    error: "Fout",
    not_found: "Geen Drooff fire+ entiteiten gevonden. Stel `device` of `entities` in.",
    editor: {
      title: "Titel (leeg = apparaatnaam)",
      device: "Apparaat",
      language: "Taal",
      lang_auto: "Automatisch (gebruikerstaal)",
      wall: "Achtergrond verbrandingskamer",
      show: "Tonen (gevonden fire+ waarden)",
      controls: "Bediening toestaan",
      layout: "Indeling",
      log_weight: "Gewicht van één blok (kg)",
      min_temperature: "Temperatuur zonder vlam (°C)",
      max_temperature: "Temperatuur voor volle vlam (°C)",
      draught_display: "Weergave schoorsteentrek",
      draught_tile: "Tegel",
      draught_gauge: "Meter (gauge)",
      layout_horizontal: "Naast elkaar",
      layout_vertical: "Onder elkaar",
      advanced: "Geavanceerd: schoorsteentrek",
      sim_start: "🔥 Vuur simuleren",
      sim_stop: "Simulatie stoppen",
      stove_picture: "Foto van de kachel (optioneel)",
      stove_pick: "Foto kiezen …",
      stove_remove: "Verwijderen",
      entities: "Entiteiten (automatisch gevonden)",
    },
    hide_labels: {
      flame: "Vlamanimatie",
      name: "Titel",
      status: "Bedrijfsstatus",
      temperature: "Temperatuur",
      target_temperature: "Doeltemperatuur",
      max_temperature: "Maximumtemperatuur",
      heating_progress: "Voortgang opstoken",
      burn_rate: "Brandvermogen",
      air_slider: "Luchtschuif",
      draught: "Schoorsteentrek",
      wood_load: "Aanbevolen houtlading",
      wood_logs: "Houtblokken-grafiek",
      door: "Deur",
      ember_burndown: "Gloed uitbranden",
      error: "Foutmelding",
      operating_time: "Bedrijfstijd",
      led: "LED",
      brightness: "LED-helderheid",
      volume: "Volume",
      wifi: "Wifi-signaal",
      ethernet: "Netwerkkabel",
    },
    graphics_labels: {temp_history: "Temperatuurverloop", timeline: "Tijdlijn verbranding", wood_usage: "Houtverbruik per dag", heating_ring: "Opstookvoortgang als ring", air_flap: "Luchtschuif als klep", temp_ring: "Temperatuur als ring" },
    walls: { chamotte: "Chamotteplaten (staand)", bricks_light: "Lichte bakstenen", bricks_dark: "Donkere bakstenen" },
  },
  fr: {
    title: "Poêle",
    status: {
      STANDBY: "Arrêt",
      REGULAR: "Fonctionnement normal",
      HEATING: "Allumage",
      WOOD_REQUIRED: "Recharger du bois",
      WOOD_URGENTLY_REQUIRED: "Recharger du bois d'urgence",
      EMBER_PRESERVATION: "Maintien des braises",
      EMBER_BURNDOWN: "Combustion des braises",
      ERROR: "Erreur",
      UNKNOWN: "Inconnu",
    },
    temperature: "Foyer",
    target: "Consigne",
    max: "Max",
    heating_progress: "Allumage",
    burn_rate: "Puissance",
    air_slider: "Registre d'air",
    draught: "Tirage",
    wood_load: "Charge de bois conseillée",
    log: "bûche",
    logs: "bûches",
    door: "Porte",
    open: "ouverte",
    closed: "fermée",
    ember: "Braises",
    ember_on: "Combustion",
    ember_off: "Maintien",
    operating_time: "Durée de fonctionnement",
    brightness: "Luminosité",
    volume: "Volume",
    wifi: "Wi-Fi",
    on: "allumée",
    off: "éteinte",
    connected: "connecté",
    disconnected: "déconnecté",
    hours: "h",
    simulation: "Simulation",
    temp_history: "Historique de température",
    timeline: "Chronologie de combustion",
    wood_usage: "Consommation de bois (estimée)",
    now: "maintenant",
    no_history: "Pas encore de données d'historique.",
    draught_target: "Optimal",
    stage: "niveau",
    draught_ok: "optimal",
    draught_low: "tirage faible",
    draught_high: "OK (tirage fort)",
    draught_negative: "surpression",
    error: "Erreur",
    not_found: "Aucune entité Drooff fire+ trouvée. Veuillez configurer `device` ou `entities`.",
    editor: {
      title: "Titre (vide = nom de l'appareil)",
      device: "Appareil",
      language: "Langue",
      lang_auto: "Automatique (langue de l'utilisateur)",
      wall: "Fond du foyer",
      show: "Afficher (valeurs fire+ détectées)",
      controls: "Autoriser les commandes",
      layout: "Disposition",
      log_weight: "Poids d'une bûche (kg)",
      min_temperature: "Température sans flamme (°C)",
      max_temperature: "Température pour pleine flamme (°C)",
      draught_display: "Affichage du tirage",
      draught_tile: "Tuile",
      draught_gauge: "Cadran (gauge)",
      layout_horizontal: "Côte à côte",
      layout_vertical: "Superposé",
      advanced: "Avancé : tirage",
      sim_start: "🔥 Simuler le feu",
      sim_stop: "Arrêter la simulation",
      stove_picture: "Photo du poêle (optionnel)",
      stove_pick: "Choisir une photo …",
      stove_remove: "Supprimer",
      entities: "Entités (détectées automatiquement)",
    },
    hide_labels: {
      flame: "Animation des flammes",
      name: "Titre",
      status: "État de fonctionnement",
      temperature: "Température",
      target_temperature: "Température de consigne",
      max_temperature: "Température maximale",
      heating_progress: "Progression de l'allumage",
      burn_rate: "Puissance",
      air_slider: "Registre d'air",
      draught: "Tirage",
      wood_load: "Charge de bois conseillée",
      wood_logs: "Graphique des bûches",
      door: "Porte",
      ember_burndown: "Combustion des braises",
      error: "Message d'erreur",
      operating_time: "Durée de fonctionnement",
      led: "LED",
      brightness: "Luminosité LED",
      volume: "Volume",
      wifi: "Signal Wi-Fi",
      ethernet: "Connexion Ethernet",
    },
    graphics_labels: {temp_history: "Historique de température", timeline: "Chronologie de combustion", wood_usage: "Bois consommé par jour", heating_ring: "Progression de l'allumage en anneau", air_flap: "Registre d'air en clapet", temp_ring: "Température en anneau" },
    walls: { chamotte: "Plaques de chamotte (verticales)", bricks_light: "Briques claires", bricks_dark: "Briques foncées" },
  },
  it: {
    title: "Stufa",
    status: {
      STANDBY: "Spenta",
      REGULAR: "Funzionamento normale",
      HEATING: "Accensione",
      WOOD_REQUIRED: "Aggiungere legna",
      WOOD_URGENTLY_REQUIRED: "Aggiungere legna subito",
      EMBER_PRESERVATION: "Mantenimento braci",
      EMBER_BURNDOWN: "Combustione braci",
      ERROR: "Errore",
      UNKNOWN: "Sconosciuto",
    },
    temperature: "Camera di combustione",
    target: "Obiettivo",
    max: "Max",
    heating_progress: "Accensione",
    burn_rate: "Potenza",
    air_slider: "Serranda aria",
    draught: "Tiraggio",
    wood_load: "Carica di legna consigliata",
    log: "ciocco",
    logs: "ciocchi",
    door: "Porta",
    open: "aperta",
    closed: "chiusa",
    ember: "Braci",
    ember_on: "Combustione",
    ember_off: "Mantenimento",
    operating_time: "Ore di esercizio",
    brightness: "Luminosità",
    volume: "Volume",
    wifi: "Wi-Fi",
    on: "acceso",
    off: "spento",
    connected: "connesso",
    disconnected: "disconnesso",
    hours: "h",
    simulation: "Simulazione",
    temp_history: "Andamento temperatura",
    timeline: "Cronologia combustione",
    wood_usage: "Consumo di legna (stimato)",
    now: "ora",
    no_history: "Nessun dato storico.",
    draught_target: "Ottimale",
    stage: "livello",
    draught_ok: "ottimale",
    draught_low: "tiraggio debole",
    draught_high: "OK (tiraggio forte)",
    draught_negative: "sovrapressione",
    error: "Errore",
    not_found: "Nessuna entità Drooff fire+ trovata. Configurare `device` o `entities`.",
    editor: {
      title: "Titolo (vuoto = nome del dispositivo)",
      device: "Dispositivo",
      language: "Lingua",
      lang_auto: "Automatica (lingua dell'utente)",
      wall: "Sfondo della camera di combustione",
      show: "Mostra (valori fire+ rilevati)",
      controls: "Consenti comandi",
      layout: "Disposizione",
      log_weight: "Peso di un ciocco (kg)",
      min_temperature: "Temperatura senza fiamma (°C)",
      max_temperature: "Temperatura per fiamma piena (°C)",
      draught_display: "Visualizzazione tiraggio",
      draught_tile: "Riquadro",
      draught_gauge: "Indicatore (gauge)",
      layout_horizontal: "Affiancati",
      layout_vertical: "Sovrapposti",
      advanced: "Avanzate: tiraggio",
      sim_start: "🔥 Simula fuoco",
      sim_stop: "Ferma simulazione",
      stove_picture: "Foto della stufa (opzionale)",
      stove_pick: "Scegli foto …",
      stove_remove: "Rimuovi",
      entities: "Entità (rilevate automaticamente)",
    },
    hide_labels: {
      flame: "Animazione fiamma",
      name: "Titolo",
      status: "Stato di funzionamento",
      temperature: "Temperatura",
      target_temperature: "Temperatura obiettivo",
      max_temperature: "Temperatura massima",
      heating_progress: "Avanzamento accensione",
      burn_rate: "Potenza",
      air_slider: "Serranda aria",
      draught: "Tiraggio",
      wood_load: "Carica di legna consigliata",
      wood_logs: "Grafica dei ciocchi",
      door: "Porta",
      ember_burndown: "Combustione braci",
      error: "Messaggio di errore",
      operating_time: "Ore di esercizio",
      led: "LED",
      brightness: "Luminosità LED",
      volume: "Volume",
      wifi: "Segnale Wi-Fi",
      ethernet: "Connessione Ethernet",
    },
    graphics_labels: {temp_history: "Andamento temperatura", timeline: "Cronologia combustione", wood_usage: "Legna consumata al giorno", heating_ring: "Accensione come anello", air_flap: "Serranda come valvola", temp_ring: "Temperatura come anello" },
    walls: { chamotte: "Lastre di chamotte (verticali)", bricks_light: "Mattoni chiari", bricks_dark: "Mattoni scuri" },
  },
  pl: {
    title: "Kominek",
    status: {
      STANDBY: "Wyłączony",
      REGULAR: "Praca normalna",
      HEATING: "Rozpalanie",
      WOOD_REQUIRED: "Dołóż drewna",
      WOOD_URGENTLY_REQUIRED: "Pilnie dołóż drewna",
      EMBER_PRESERVATION: "Podtrzymanie żaru",
      EMBER_BURNDOWN: "Dopalanie żaru",
      ERROR: "Błąd",
      UNKNOWN: "Nieznany",
    },
    temperature: "Komora spalania",
    target: "Cel",
    max: "Maks.",
    heating_progress: "Rozpalanie",
    burn_rate: "Moc spalania",
    air_slider: "Przepustnica powietrza",
    draught: "Ciąg kominowy",
    wood_load: "Zalecany załadunek drewna",
    log: "polano",
    logs: "polana",
    door: "Drzwi",
    open: "otwarte",
    closed: "zamknięte",
    ember: "Żar",
    ember_on: "Dopalanie",
    ember_off: "Podtrzymanie",
    operating_time: "Czas pracy",
    brightness: "Jasność",
    volume: "Głośność",
    wifi: "Wi-Fi",
    on: "wł.",
    off: "wył.",
    connected: "połączono",
    disconnected: "rozłączono",
    hours: "h",
    simulation: "Symulacja",
    temp_history: "Przebieg temperatury",
    timeline: "Oś czasu spalania",
    wood_usage: "Zużycie drewna (szacunkowe)",
    now: "teraz",
    no_history: "Brak danych historycznych.",
    draught_target: "Optymalnie",
    stage: "stopień",
    draught_ok: "optymalny",
    draught_low: "słaby ciąg",
    draught_high: "OK (silny ciąg)",
    draught_negative: "nadciśnienie",
    error: "Błąd",
    not_found: "Nie znaleziono encji Drooff fire+. Skonfiguruj `device` lub `entities`.",
    editor: {
      title: "Tytuł (pusty = nazwa urządzenia)",
      device: "Urządzenie",
      language: "Język",
      lang_auto: "Automatycznie (język użytkownika)",
      wall: "Tło komory spalania",
      show: "Pokaż (wykryte wartości fire+)",
      controls: "Zezwól na sterowanie",
      layout: "Układ",
      log_weight: "Waga jednego polana (kg)",
      min_temperature: "Temperatura bez płomienia (°C)",
      max_temperature: "Temperatura pełnego płomienia (°C)",
      draught_display: "Wyświetlanie ciągu",
      draught_tile: "Kafelek",
      draught_gauge: "Wskaźnik (gauge)",
      layout_horizontal: "Obok siebie",
      layout_vertical: "Jeden pod drugim",
      advanced: "Zaawansowane: ciąg kominowy",
      sim_start: "🔥 Symuluj ogień",
      sim_stop: "Zatrzymaj symulację",
      stove_picture: "Zdjęcie kominka (opcjonalnie)",
      stove_pick: "Wybierz zdjęcie …",
      stove_remove: "Usuń",
      entities: "Encje (wykryte automatycznie)",
    },
    hide_labels: {
      flame: "Animacja płomienia",
      name: "Tytuł",
      status: "Stan pracy",
      temperature: "Temperatura",
      target_temperature: "Temperatura docelowa",
      max_temperature: "Temperatura maksymalna",
      heating_progress: "Postęp rozpalania",
      burn_rate: "Moc spalania",
      air_slider: "Przepustnica powietrza",
      draught: "Ciąg kominowy",
      wood_load: "Zalecany załadunek drewna",
      wood_logs: "Grafika polan",
      door: "Drzwi",
      ember_burndown: "Dopalanie żaru",
      error: "Komunikat błędu",
      operating_time: "Czas pracy",
      led: "LED",
      brightness: "Jasność LED",
      volume: "Głośność",
      wifi: "Sygnał Wi-Fi",
      ethernet: "Połączenie Ethernet",
    },
    graphics_labels: {temp_history: "Przebieg temperatury", timeline: "Oś czasu spalania", wood_usage: "Zużycie drewna dziennie", heating_ring: "Postęp rozpalania jako pierścień", air_flap: "Przepustnica jako klapa", temp_ring: "Temperatura jako pierścień" },
    walls: { chamotte: "Płyty szamotowe (pionowe)", bricks_light: "Jasna cegła", bricks_dark: "Ciemna cegła" },
  },
  cs: {
    title: "Krbová kamna",
    status: {
      STANDBY: "Vypnuto",
      REGULAR: "Běžný provoz",
      HEATING: "Zatápění",
      WOOD_REQUIRED: "Přiložit dřevo",
      WOOD_URGENTLY_REQUIRED: "Naléhavě přiložit dřevo",
      EMBER_PRESERVATION: "Udržování žhavých uhlíků",
      EMBER_BURNDOWN: "Dohořívání uhlíků",
      ERROR: "Chyba",
      UNKNOWN: "Neznámý",
    },
    temperature: "Spalovací komora",
    target: "Cíl",
    max: "Max",
    heating_progress: "Zatápění",
    burn_rate: "Výkon",
    air_slider: "Šoupátko vzduchu",
    draught: "Komínový tah",
    wood_load: "Doporučená dávka dřeva",
    log: "poleno",
    logs: "polen",
    door: "Dvířka",
    open: "otevřená",
    closed: "zavřená",
    ember: "Uhlíky",
    ember_on: "Dohořívání",
    ember_off: "Udržování",
    operating_time: "Doba provozu",
    brightness: "Jas",
    volume: "Hlasitost",
    wifi: "Wi-Fi",
    on: "zap.",
    off: "vyp.",
    connected: "připojeno",
    disconnected: "odpojeno",
    hours: "h",
    simulation: "Simulace",
    temp_history: "Průběh teploty",
    timeline: "Časová osa hoření",
    wood_usage: "Spotřeba dřeva (odhad)",
    now: "nyní",
    no_history: "Zatím žádná historická data.",
    draught_target: "Optimum",
    stage: "stupeň",
    draught_ok: "optimální",
    draught_low: "slabý tah",
    draught_high: "OK (silný tah)",
    draught_negative: "přetlak",
    error: "Chyba",
    not_found: "Nenalezeny žádné entity Drooff fire+. Nastavte `device` nebo `entities`.",
    editor: {
      title: "Název (prázdné = název zařízení)",
      device: "Zařízení",
      language: "Jazyk",
      lang_auto: "Automaticky (jazyk uživatele)",
      wall: "Pozadí spalovací komory",
      show: "Zobrazit (nalezené hodnoty fire+)",
      controls: "Povolit ovládání",
      layout: "Rozvržení",
      log_weight: "Hmotnost jednoho polena (kg)",
      min_temperature: "Teplota bez plamene (°C)",
      max_temperature: "Teplota pro plný plamen (°C)",
      draught_display: "Zobrazení tahu",
      draught_tile: "Dlaždice",
      draught_gauge: "Ručičkový ukazatel (gauge)",
      layout_horizontal: "Vedle sebe",
      layout_vertical: "Pod sebou",
      advanced: "Pokročilé: komínový tah",
      sim_start: "🔥 Simulovat oheň",
      sim_stop: "Ukončit simulaci",
      stove_picture: "Fotka kamen (volitelné)",
      stove_pick: "Vybrat fotku …",
      stove_remove: "Odebrat",
      entities: "Entity (nalezeny automaticky)",
    },
    hide_labels: {
      flame: "Animace plamene",
      name: "Název",
      status: "Provozní stav",
      temperature: "Teplota",
      target_temperature: "Cílová teplota",
      max_temperature: "Maximální teplota",
      heating_progress: "Průběh zatápění",
      burn_rate: "Výkon",
      air_slider: "Šoupátko vzduchu",
      draught: "Komínový tah",
      wood_load: "Doporučená dávka dřeva",
      wood_logs: "Grafika polen",
      door: "Dvířka",
      ember_burndown: "Dohořívání uhlíků",
      error: "Chybová zpráva",
      operating_time: "Doba provozu",
      led: "LED",
      brightness: "Jas LED",
      volume: "Hlasitost",
      wifi: "Signál Wi-Fi",
      ethernet: "Připojení Ethernet",
    },
    graphics_labels: {temp_history: "Průběh teploty", timeline: "Časová osa hoření", wood_usage: "Spotřeba dřeva za den", heating_ring: "Zatápění jako kruh", air_flap: "Šoupátko jako klapka", temp_ring: "Teplota jako kruh" },
    walls: { chamotte: "Šamotové desky (svislé)", bricks_light: "Světlé cihly", bricks_dark: "Tmavé cihly" },
  },
  da: {
    title: "Brændeovn",
    status: {
      STANDBY: "Slukket",
      REGULAR: "Normal drift",
      HEATING: "Optænding",
      WOOD_REQUIRED: "Læg brænde på",
      WOOD_URGENTLY_REQUIRED: "Læg brænde på nu",
      EMBER_PRESERVATION: "Gløder bevares",
      EMBER_BURNDOWN: "Gløder brænder ud",
      ERROR: "Fejl",
      UNKNOWN: "Ukendt",
    },
    temperature: "Brændkammer",
    target: "Mål",
    max: "Maks.",
    heating_progress: "Optænding",
    burn_rate: "Effekt",
    air_slider: "Luftspjæld",
    draught: "Skorstenstræk",
    wood_load: "Anbefalet brændemængde",
    log: "brændestykke",
    logs: "brændestykker",
    door: "Låge",
    open: "åben",
    closed: "lukket",
    ember: "Gløder",
    ember_on: "Udbrænding",
    ember_off: "Bevar",
    operating_time: "Driftstid",
    brightness: "Lysstyrke",
    volume: "Lydstyrke",
    wifi: "Wi-Fi",
    on: "til",
    off: "fra",
    connected: "forbundet",
    disconnected: "afbrudt",
    hours: "t",
    simulation: "Simulering",
    temp_history: "Temperaturforløb",
    timeline: "Tidslinje for forbrænding",
    wood_usage: "Brændeforbrug (anslået)",
    now: "nu",
    no_history: "Ingen historikdata endnu.",
    draught_target: "Optimalt",
    stage: "trin",
    draught_ok: "optimalt",
    draught_low: "svagt træk",
    draught_high: "OK (kraftigt træk)",
    draught_negative: "overtryk",
    error: "Fejl",
    not_found: "Ingen Drooff fire+ enheder fundet. Angiv `device` eller `entities`.",
    editor: {
      title: "Titel (tom = enhedsnavn)",
      device: "Enhed",
      language: "Sprog",
      lang_auto: "Automatisk (brugerens sprog)",
      wall: "Baggrund i brændkammeret",
      show: "Vis (fundne fire+ værdier)",
      controls: "Tillad betjening",
      layout: "Layout",
      log_weight: "Vægt af ét brændestykke (kg)",
      min_temperature: "Temperatur uden flamme (°C)",
      max_temperature: "Temperatur for fuld flamme (°C)",
      draught_display: "Visning af træk",
      draught_tile: "Felt",
      draught_gauge: "Viserinstrument (gauge)",
      layout_horizontal: "Side om side",
      layout_vertical: "Under hinanden",
      advanced: "Avanceret: skorstenstræk",
      sim_start: "🔥 Simuler ild",
      sim_stop: "Stop simulering",
      stove_picture: "Billede af ovnen (valgfrit)",
      stove_pick: "Vælg billede …",
      stove_remove: "Fjern",
      entities: "Enheder (fundet automatisk)",
    },
    hide_labels: {
      flame: "Flammeanimation",
      name: "Titel",
      status: "Driftsstatus",
      temperature: "Temperatur",
      target_temperature: "Måltemperatur",
      max_temperature: "Maksimal temperatur",
      heating_progress: "Optændingsforløb",
      burn_rate: "Effekt",
      air_slider: "Luftspjæld",
      draught: "Skorstenstræk",
      wood_load: "Anbefalet brændemængde",
      wood_logs: "Brændegrafik",
      door: "Låge",
      ember_burndown: "Udbrænding af gløder",
      error: "Fejlmeddelelse",
      operating_time: "Driftstid",
      led: "LED",
      brightness: "LED-lysstyrke",
      volume: "Lydstyrke",
      wifi: "Wi-Fi-signal",
      ethernet: "Ethernet-forbindelse",
    },
    graphics_labels: {temp_history: "Temperaturforløb", timeline: "Tidslinje for forbrænding", wood_usage: "Brændeforbrug pr. dag", heating_ring: "Optænding som ring", air_flap: "Luftspjæld som klap", temp_ring: "Temperatur som ring" },
    walls: { chamotte: "Chamotteplader (stående)", bricks_light: "Lyse mursten", bricks_dark: "Mørke mursten" },
  },
};

const STATUS_COLOR = {
  STANDBY: "#8a8a8a",
  REGULAR: "#43a047",
  HEATING: "#fb8c00",
  WOOD_REQUIRED: "#fbc02d",
  WOOD_URGENTLY_REQUIRED: "#f4511e",
  EMBER_PRESERVATION: "#8e24aa",
  EMBER_BURNDOWN: "#ef6c00",
  ERROR: "#e53935",
  UNKNOWN: "#8a8a8a",
};

/* card language: configured one, otherwise the user's language */
const lang = (hass, cfg) => {
  const l = cfg && cfg.language && cfg.language !== "auto" ? cfg.language : (hass && hass.language) || "en";
  return String(l).toLowerCase().split(/[-_]/)[0] || "en";
};

/* fire simulation for the preview: one cycle through all burning phases */
const LANG_NAMES = {
  de: "Deutsch",
  en: "English",
  nl: "Nederlands",
  fr: "Français",
  it: "Italiano",
  pl: "Polski",
  cs: "Čeština",
  da: "Dansk",
};

const deepMerge = (a, b) => {
  const o = { ...a };
  for (const [k, v] of Object.entries(b || {})) {
    o[k] = v && typeof v === "object" && !Array.isArray(v) ? deepMerge(a && typeof a[k] === "object" ? a[k] : {}, v) : v;
  }
  return o;
};
/* texts: English as base, the chosen language over it, custom `translations` on top */
const _trCache = new Map();
const tr = (hass, cfg) => {
  const code = lang(hass, cfg);
  const custom = (cfg && cfg.translations) || null;
  const key = code + "|" + (custom ? JSON.stringify(custom) : "");
  if (!_trCache.has(key)) {
    if (_trCache.size > 20) _trCache.clear();
    _trCache.set(key, deepMerge(deepMerge(I18N.en, I18N[code] || {}), custom && typeof custom === "object" ? custom : {}));
  }
  return _trCache.get(key);
};

const SIM_EVENT = "drooff-fireplus-simulate";
const SIM_PHASES = [
  /* d0/d1: chimney draught in Pa, negative = draught (the hotter the flue, the stronger) */
  { status: "HEATING", t0: 60, t1: 360, air: 100, dur: 9, d0: -3, d1: -13 },
  { status: "REGULAR", t0: 360, t1: 580, air: 45, dur: 9, d0: -13, d1: -17 },
  { status: "WOOD_REQUIRED", t0: 560, t1: 380, air: 70, dur: 8, wood: 1.8, d0: -17, d1: -13 },
  { status: "WOOD_URGENTLY_REQUIRED", t0: 380, t1: 280, air: 90, dur: 6, wood: 2.7, d0: -13, d1: -10 },
  { status: "EMBER_BURNDOWN", t0: 280, t1: 230, air: 100, dur: 8, ember: true, d0: -10, d1: -8 },
  { status: "EMBER_PRESERVATION", t0: 230, t1: 170, air: 0, dur: 8, d0: -8, d1: -5 },
];
const SIM_CYCLE = SIM_PHASES.reduce((a, ph) => a + ph.dur, 0);
const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
const num = (s) => {
  if (!s) return NaN;
  const v = parseFloat(s.state);
  return Number.isFinite(v) ? v : NaN;
};
const usable = (s) => s && s.state !== "unavailable" && s.state !== "unknown";
const esc = (t) =>
  String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

/* ------------------------------------------------------- fire renderer */

/* colour of a flame particle over its life (0 = born, 1 = dead) */
const FLAME_STOPS = [
  [0.0, [255, 250, 232]],
  [0.1, [255, 228, 150]],
  [0.28, [255, 170, 55]],
  [0.52, [238, 92, 18]],
  [0.78, [150, 32, 6]],
  [1.0, [55, 10, 0]],
];
/* colour of a coal by heat (0 = dark, 1 = white hot) */
const EMBER_STOPS = [
  [0.0, [40, 6, 0]],
  [0.3, [140, 18, 0]],
  [0.6, [225, 70, 8]],
  [0.85, [255, 150, 40]],
  [1.0, [255, 225, 140]],
];

const lerpStops = (stops, t) => {
  t = clamp(t);
  for (let k = 1; k < stops.length; k++) {
    if (t <= stops[k][0]) {
      const [t0, c0] = stops[k - 1];
      const [t1, c1] = stops[k];
      const f = (t - t0) / (t1 - t0);
      return c0.map((v, j) => Math.round(v + (c1[j] - v) * f));
    }
  }
  return stops[stops.length - 1][1];
};

const makeSprite = (rgb, size = 64) => {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  const r = size / 2;
  const grd = g.createRadialGradient(r, r, 0, r, r, r);
  const [R, G, B] = rgb;
  grd.addColorStop(0, `rgba(${R},${G},${B},1)`);
  grd.addColorStop(0.35, `rgba(${R},${G},${B},0.55)`);
  grd.addColorStop(0.7, `rgba(${R},${G},${B},0.12)`);
  grd.addColorStop(1, `rgba(${R},${G},${B},0)`);
  g.fillStyle = grd;
  g.fillRect(0, 0, size, size);
  return c;
};

const gauss = () => {
  let u = 0;
  for (let k = 0; k < 3; k++) u += Math.random();
  return (u - 1.5) / 0.5;
};

const noise1 = (a) => (Math.sin(a) + Math.sin(1.73 * a + 1.3) * 0.6 + Math.sin(2.97 * a + 2.1) * 0.35) / 1.95;

const W = 200;
const H = 250;

/* look of the combustion chamber */
const WALL_STYLES = {
  chamotte: { plate: true, plateHeight: 150, color: [234, 224, 204], vary: 7, joint: 0.45, jointColor: "rgb(150,138,120)" },
  bricks_light: { plate: false, color: [236, 229, 214], vary: 16, joint: 0.6, jointColor: "rgb(110,100,88)" },
  bricks_dark: { plate: false, color: [52, 42, 37], vary: 10, joint: 0.6, jointColor: "rgb(150,112,82)", dark: true },
};
const BED_Y = 214;

class FireRenderer {
  constructor(canvas) {
    this.c = canvas;
    this.ctx = canvas.getContext("2d");
    this.flames = [];
    this.sparks = [];
    this.acc = 0;
    this.sacc = 0;
    this.t = 0;
    this.target = { i: 0, e: 0, mode: "off", fuel: 1 };
    this.cur = { i: 0, e: 0, fuel: 1 };
    this.flameSprites = Array.from({ length: 48 }, (_, k) => makeSprite(lerpStops(FLAME_STOPS, k / 47)));
    this.emberSprites = Array.from({ length: 32 }, (_, k) => makeSprite(lerpStops(EMBER_STOPS, k / 31), 32));
    this.coals = this._makeCoals();
    /* flame tongues: fixed sources along the logs, each with its own rhythm */
    this.sources = [-0.95, -0.7, -0.45, -0.2, 0, 0.22, 0.48, 0.72, 0.96].map((o) => ({
      o,
      ph: Math.random() * 100,
      sp: 0.6 + Math.random() * 0.8,
      w: 1 - Math.abs(o) * 0.55,
    }));
    this.scale = 1;
    this.visible = true;
    this._loop = this._loop.bind(this);
  }

  _makeCoals() {
    const coals = [];
    for (let k = 0; k < 130; k++) {
      const x = 100 + gauss() * 34;
      if (x < 28 || x > 172) continue;
      /* pile is higher in the middle */
      const top = BED_Y + 2 - 16 * Math.exp(-(((x - 100) / 38) ** 2));
      const y = top + Math.random() * (234 - top);
      const pts = Array.from({ length: 7 }, (_, j) => {
        const a = (j / 7) * Math.PI * 2;
        const rr = 0.7 + Math.random() * 0.45;
        return [Math.cos(a) * rr, Math.sin(a) * rr * 0.75];
      });
      coals.push({
        x,
        y,
        pts,
        r: 3 + Math.random() * 4,
        rx: 1 + Math.random() * 0.5,
        rot: Math.random() * Math.PI,
        ph: Math.random() * 100,
        sp: 0.015 + Math.random() * 0.04,
        heat: 0.55 + Math.random() * 0.45,
        depth: (y - top) / (234 - top + 0.01),
      });
    }
    return coals.sort((a, b) => a.y - b.y);
  }

  set(i, e, mode, fuel = 1) {
    this.target = { i, e, mode, fuel };
    this._kick();
  }

  attach() {
    this.attached = true;
    this._kick();
  }

  detach() {
    this.attached = false;
  }

  setVisible(v) {
    this.visible = v;
    this._kick();
  }

  _kick() {
    if (!this.running && this.attached && this.visible) {
      this.running = true;
      this.last = performance.now();
      requestAnimationFrame(this._loop);
    }
  }

  _resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = this.c.clientWidth;
    const h = this.c.clientHeight || (w * H) / W;
    if (!w || !h) return false;
    const pw = Math.round(w * dpr);
    const ph = Math.round(h * dpr);
    if (this.c.width !== pw || this.c.height !== ph || !this.walls) {
      this.c.width = pw;
      this.c.height = ph;
      this.scale = pw / W;
      /* the scene is anchored at the bottom: y = 250 is the lower window edge */
      this.top = H - ph / this.scale;
      this._buildWalls(pw, ph);
    }
    return true;
  }

  /* fire-clay (Schamotte) chamber: white bricks on the back wall, angled side walls */
  setWall(wall) {
    if (wall !== this.wall) {
      this.wall = wall;
      this.walls = null;
    }
  }

  _buildWalls(pw, ph) {
    const mk = () => {
      const c = document.createElement("canvas");
      c.width = pw;
      c.height = ph;
      return c;
    };
    this.walls = mk();
    this.light = mk();
    const g = this.walls.getContext("2d");
    g.setTransform(this.scale, 0, 0, this.scale, 0, -this.top * this.scale);
    const top = this.top - 2;
    const VX = 100;
    const VY = 150;
    const BX0 = 38;
    const BX1 = 162;
    const FLOOR = 206;
    const s1 = (VX - 0) / (VX - BX0);
    const proj = (u, yb, side) => {
      /* u = 0 at the back corner, 1 at the window plane */
      const s = 1 + u * (s1 - 1);
      const bx = side < 0 ? BX0 : BX1;
      return [VX + (bx - VX) * s, VY + (yb - VY) * s];
    };
    let seed = 7;
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    const style = WALL_STYLES[this.wall] || WALL_STYLES.chamotte;
    const tile = (shade) => {
      const v = (rnd() - 0.5) * style.vary;
      const warm = rnd() * 6;
      const [R, G, B] = style.color;
      return `rgb(${Math.round(R * shade + v + warm)},${Math.round(G * shade + v)},${Math.round(B * shade + v - warm)})`;
    };
    const quad = (pts) => {
      g.beginPath();
      pts.forEach((pt, k) => (k ? g.lineTo(...pt) : g.moveTo(...pt)));
      g.closePath();
      g.fill();
    };
    const J = style.joint;
    const ytopSide = VY + (top - VY) / s1 - 40;

    /* joints = background of each wall */
    g.fillStyle = style.jointColor;
    g.fillRect(BX0, top, BX1 - BX0, FLOOR - top);
    for (const side of [-1, 1]) {
      const bx = side < 0 ? BX0 : BX1;
      const wx = side < 0 ? 0 : W;
      quad([[bx, ytopSide], [bx, FLOOR], [wx, VY + (FLOOR - VY) * s1], [wx, top - 400]]);
    }

    /* panels: back wall in x, side walls in depth u (0 = back corner, 1 = window) */
    const back = (x0, x1, y0, y1, shade) => {
      g.fillStyle = tile(shade);
      g.fillRect(x0 + J, y1 + J, x1 - x0 - 2 * J, y0 - y1 - 2 * J);
      if (style.plate) {
        /* slight relief at the plate edges */
        const gr = g.createLinearGradient(x0, 0, x1, 0);
        gr.addColorStop(0, "rgba(0,0,0,0.10)");
        gr.addColorStop(0.12, "rgba(0,0,0,0)");
        gr.addColorStop(0.88, "rgba(0,0,0,0)");
        gr.addColorStop(1, "rgba(0,0,0,0.12)");
        g.fillStyle = gr;
        g.fillRect(x0 + J, y1 + J, x1 - x0 - 2 * J, y0 - y1 - 2 * J);
      }
    };
    const sideP = (u0, u1, y0, y1, side, shade) => {
      const pad = J / 60;
      g.fillStyle = tile(shade);
      quad([proj(u0 + pad, y0 - J, side), proj(u1 - pad, y0 - J, side), proj(u1 - pad, y1 + J, side), proj(u0 + pad, y1 + J, side)]);
    };

    if (style.plate) {
      /* upright fire-clay plates (hochkant), three on the back wall, two per side wall */
      const PH = style.plateHeight;
      const cols = 3;
      const pw = (BX1 - BX0) / cols;
      for (let y = FLOOR; y > top - PH; y -= PH) {
        for (let c = 0; c < cols; c++) back(BX0 + c * pw, BX0 + (c + 1) * pw, y, y - PH, 1);
      }
      for (const side of [-1, 1]) {
        for (let y = FLOOR; y > ytopSide - 200; y -= PH) {
          sideP(0, 0.5, y, y - PH, side, 0.88);
          sideP(0.5, 1, y, y - PH, side, 0.88);
        }
      }
    } else {
      const RH = 17;
      const BW = 41;
      for (let row = 0, y = FLOOR; y > top; row++, y -= RH) {
        const off = row % 2 ? -BW / 2 : 0;
        for (let x = BX0 + off; x < BX1; x += BW) {
          const x0 = Math.max(BX0, x);
          const x1 = Math.min(BX1, x + BW);
          if (x1 - x0 > 2) back(x0, x1, y, y - RH, 1);
        }
      }
      const us = [0, 0.3, 0.62, 1];
      for (const side of [-1, 1]) {
        for (let row = 0, y = FLOOR; y > ytopSide - 200; row++, y -= RH) {
          const shift = row % 2 ? 0.16 : 0;
          for (let k = -1; k < us.length - 1; k++) {
            const u0 = clamp((k < 0 ? 0 : us[k]) + (k < 0 ? 0 : shift));
            const u1 = clamp(us[k + 1] + shift);
            if (u1 - u0 >= 0.02) sideP(u0, u1, y, y - RH, side, 0.86);
          }
        }
      }
    }

    /* hearth floor with grate */
    g.fillStyle = "#4a4541";
    g.beginPath();
    g.moveTo(BX0, FLOOR);
    g.lineTo(BX1, FLOOR);
    g.lineTo(W, VY + (FLOOR - VY) * s1);
    g.lineTo(W, 260);
    g.lineTo(0, 260);
    g.lineTo(0, VY + (FLOOR - VY) * s1);
    g.closePath();
    g.fill();

    /* fine speckles of the fire clay */
    for (let k = 0; k < 900; k++) {
      const x = rnd() * W;
      const y = top + rnd() * (FLOOR - top);
      g.fillStyle = `rgba(120,100,80,${0.08 + rnd() * 0.12})`;
      g.fillRect(x, y, 0.7, 0.7);
    }

    /* soot: darker towards the baffle plate and above the fire */
    let sg = g.createLinearGradient(0, top, 0, FLOOR);
    sg.addColorStop(0, "rgba(25,20,16,0.72)");
    sg.addColorStop(0.45, "rgba(40,30,22,0.22)");
    sg.addColorStop(1, "rgba(40,30,22,0)");
    g.fillStyle = sg;
    g.fillRect(0, top, W, FLOOR - top);
    sg = g.createRadialGradient(100, 150, 5, 100, 150, 70);
    sg.addColorStop(0, "rgba(30,22,16,0.28)");
    sg.addColorStop(1, "rgba(30,22,16,0)");
    g.fillStyle = sg;
    g.fillRect(0, top, W, FLOOR - top);
    /* baffle plate at the top of the chamber */
    g.fillStyle = "#151210";
    g.fillRect(0, top, W, 6);
  }

  _loop(ts) {
    if (!this.attached || !this.visible) {
      this.running = false;
      return;
    }
    /* 30 fps are plenty for fire; a cold stove only needs a few frames per second */
    const idle =
      this.target.i < 0.01 && this.target.e < 0.01 && this.cur.i < 0.01 && this.cur.e < 0.01 && !this.flames.length && !this.sparks.length;
    if (ts - this.last < (idle ? 250 : 32)) {
      requestAnimationFrame(this._loop);
      return;
    }
    const dt = Math.min(3, (ts - this.last) / 16.667 || 1);
    this.last = ts;
    if (this._resize()) {
      this._step(dt);
      this._draw();
    }
    requestAnimationFrame(this._loop);
  }

  _step(dt) {
    this.t += dt;
    const cur = this.cur;
    const tg = this.target;
    const k = 1 - Math.pow(0.985, dt);
    cur.i += (tg.i - cur.i) * k;
    cur.e += (tg.e - cur.e) * k;
    cur.fuel += (tg.fuel - cur.fuel) * k;
    const i = cur.i;

    /* emit flame particles */
    this.acc += (i > 0.01 ? 1.5 + i * 11 : 0) * dt;
    const half = 14 + 52 * i;
    while (this.acc >= 1 && this.flames.length < 700) {
      this.acc -= 1;
      /* pick a tongue, weighted towards the middle */
      let src;
      do src = this.sources[Math.floor(Math.random() * this.sources.length)];
      while (Math.random() > src.w);
      const str = 0.55 + 0.45 * noise1(this.t * 0.012 * src.sp + src.ph);
      const x = 100 + src.o * half + gauss() * (2.5 + 3 * i);
      this.flames.push({
        x,
        y: BED_Y - 3 + Math.random() * 5 - 8 * Math.exp(-(((x - 100) / 30) ** 2)) * cur.fuel,
        vx: (100 - x) * 0.004 + gauss() * 0.08,
        vy: -(0.5 + 1.5 * i) * (0.75 + 0.5 * Math.random()),
        age: 0,
        life: (20 + 78 * i) * (0.6 + 0.5 * Math.random()) * src.w * str,
        size: (5 + 10 * i) * (0.7 + 0.6 * Math.random()),
        seed: src.ph,
        sp: src.sp,
      });
    }
    if (this.acc > 1) this.acc = 1;

    const t = this.t;
    for (const p of this.flames) {
      p.age += dt;
      p.vy -= 0.035 * (0.4 + i) * dt;
      p.vx += noise1(t * 0.05 * p.sp + p.y * 0.035 + p.seed) * 0.06 * dt;
      p.vx += (100 - p.x) * 0.0006 * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
    }
    this.flames = this.flames.filter((p) => p.age < p.life);

    /* sparks */
    const sparkRate = i > 0.4 ? (i - 0.4) * 0.25 : this.target.mode === "burndown" ? 0.02 : 0;
    this.sacc += sparkRate * dt;
    while (this.sacc >= 1) {
      this.sacc -= 1;
      this.sparks.push({
        x: 100 + gauss() * 22,
        y: BED_Y - 6,
        vx: gauss() * 0.3,
        vy: -(1.5 + Math.random() * 2.2),
        age: 0,
        life: 50 + Math.random() * 60,
        seed: Math.random() * 100,
      });
    }
    for (const s of this.sparks) {
      s.age += dt;
      s.vy *= 0.995;
      s.vx += noise1(t * 0.1 + s.seed) * 0.08 * dt;
      s.x += s.vx * dt;
      s.y += s.vy * dt;
    }
    this.sparks = this.sparks.filter((s) => s.age < s.life && s.y > this.top - 10);
  }

  _draw() {
    const g = this.ctx;
    const { i, e, fuel } = this.cur;
    const t = this.t;
    const mode = this.target.mode;
    g.globalCompositeOperation = "source-over";
    g.globalAlpha = 1;

    /* light level of the chamber, flickers with the flames */
    const flick = 0.85 + 0.15 * noise1(t * 0.21) * (i > 0.05 ? 1 : 0.3);
    const light = clamp((i * 0.95 + e * 0.3) * flick);

    /* light map (warm light from the fire) multiplied with the white fire-clay walls */
    const lg = this.light.getContext("2d");
    lg.setTransform(1, 0, 0, 1, 0, 0);
    lg.globalCompositeOperation = "source-over";
    lg.globalAlpha = 1;
    lg.fillStyle = "rgb(72,70,70)";
    lg.fillRect(0, 0, this.light.width, this.light.height);
    lg.setTransform(this.scale, 0, 0, this.scale, 0, -this.top * this.scale);
    lg.globalCompositeOperation = "lighter";
    const cx = 100 + noise1(t * 0.03) * 4 * i;
    const cy = BED_Y - 10 - 25 * i;
    let rg = lg.createRadialGradient(cx, cy, 4, cx, cy, 90 + 130 * light);
    rg.addColorStop(0, `rgba(255,214,150,${light})`);
    rg.addColorStop(0.35, `rgba(255,150,70,${0.85 * light})`);
    rg.addColorStop(1, "rgba(160,50,10,0)");
    lg.fillStyle = rg;
    lg.fillRect(-10, this.top - 10, W + 20, H - this.top + 20);
    lg.globalCompositeOperation = "multiply";
    lg.setTransform(1, 0, 0, 1, 0, 0);
    lg.drawImage(this.walls, 0, 0);

    g.setTransform(1, 0, 0, 1, 0, 0);
    g.drawImage(this.light, 0, 0);
    g.setTransform(this.scale, 0, 0, this.scale, 0, -this.top * this.scale);

    /* coal bed */
    this._drawCoals(g, e, i, mode, t);

    g.globalCompositeOperation = "lighter";
    /* blue base where the gas ignites */
    if (i > 0.15) {
      g.globalAlpha = clamp((i - 0.15) * 0.4);
      const bl = g.createRadialGradient(100, BED_Y - 2, 1, 100, BED_Y - 2, 30 + 30 * i);
      bl.addColorStop(0, "rgba(90,140,255,0.5)");
      bl.addColorStop(1, "rgba(40,60,200,0)");
      g.fillStyle = bl;
      g.beginPath();
      g.ellipse(100, BED_Y - 4, 24 + 30 * i, 5, 0, 0, Math.PI * 2);
      g.fill();
    }
    g.globalCompositeOperation = "source-over";
    g.globalAlpha = 1;
    /* logs (not in ember modes) */
    if (mode !== "ember" && mode !== "burndown") this._drawLogs(g, i, fuel, mode);

    /* flames */
    g.globalCompositeOperation = "lighter";
    for (const p of this.flames) {
      const k = p.age / p.life;
      const s = p.size * (1 - k * 0.7);
      const a = (k < 0.1 ? k / 0.1 : 1) * (1 - k) * (0.3 + 0.12 * i);
      if (a <= 0.003) continue;
      const spr = this.flameSprites[Math.min(47, Math.floor((0.06 + k * 0.94) * 48))];
      g.globalAlpha = a;
      const stretch = 1.7 + Math.min(1.4, -p.vy * 0.55);
      g.drawImage(spr, p.x - s * 0.65, p.y - s * stretch * 0.62, s * 1.3, s * stretch);
    }
    /* sparks */
    for (const s of this.sparks) {
      const k = s.age / s.life;
      g.globalAlpha = (1 - k) * (0.6 + 0.4 * Math.sin(s.age * 0.8 + s.seed));
      g.drawImage(this.emberSprites[31 - Math.floor(k * 12)], s.x - 2.2, s.y - 2.2, 4.4, 4.4);
    }

    /* subtle haze at top */
    g.globalCompositeOperation = "source-over";
    g.globalAlpha = 1;
    rg = g.createLinearGradient(0, this.top, 0, this.top + 50);
    rg.addColorStop(0, "rgba(0,0,0,0.5)");
    rg.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = rg;
    g.fillRect(0, this.top, W, 50);
  }

  _drawCoals(g, e, i, mode, t) {
    const heatMul = mode === "burndown" ? 1.05 : mode === "ember" ? 0.8 : 0.85;
    const speedMul = mode === "burndown" ? 1.8 : mode === "ember" ? 0.6 : 1;
    /* ash */
    g.fillStyle = "#2a2522";
    g.beginPath();
    g.ellipse(100, 238, 92, 12, 0, 0, Math.PI * 2);
    g.fill();

    const bedLevel = clamp(e + i * 0.4);
    for (const c of this.coals) {
      const n = noise1(t * c.sp * speedMul + c.ph);
      const heat = clamp(bedLevel * c.heat * heatMul * (0.72 + 0.28 * n) * (1 - c.depth * 0.35));
      /* coal body */
      const body = lerpStops(EMBER_STOPS, heat * 0.85);
      const dark = 1 - heat;
      g.globalCompositeOperation = "source-over";
      g.globalAlpha = 1;
      g.fillStyle = `rgb(${Math.round(body[0] * heat + 26 * dark)},${Math.round(body[1] * heat + 20 * dark)},${Math.round(
        body[2] * heat + 18 * dark
      )})`;
      g.beginPath();
      c.pts.forEach(([px, py], j) => {
        const X = c.x + (px * Math.cos(c.rot) - py * Math.sin(c.rot)) * c.r * c.rx;
        const Y = c.y + (px * Math.sin(c.rot) + py * Math.cos(c.rot)) * c.r * 0.8;
        j ? g.lineTo(X, Y) : g.moveTo(X, Y);
      });
      g.closePath();
      g.fill();
      /* dark ash skin on cooler coals */
      g.strokeStyle = `rgba(20,14,12,${0.25 + 0.5 * (1 - heat)})`;
      g.lineWidth = 0.8;
      g.stroke();
      /* glow */
      if (heat > 0.05) {
        g.globalCompositeOperation = "lighter";
        g.globalAlpha = heat * 0.8;
        const s = c.r * 4.6;
        g.drawImage(this.emberSprites[Math.min(31, Math.floor(heat * 32))], c.x - s / 2, c.y - s / 2, s, s);
      }
    }
    /* small dancing flames over the embers in burndown mode */
    if (mode === "burndown" && e > 0.3) {
      g.globalCompositeOperation = "lighter";
      for (let k = 0; k < 7; k++) {
        const x = 52 + k * 16 + noise1(t * 0.02 + k * 7) * 6;
        const h = 6 + 8 * clamp(noise1(t * 0.05 + k * 3) * 0.5 + 0.5);
        g.globalAlpha = 0.25 * e;
        const spr = this.flameSprites[16 + k];
        g.drawImage(spr, x - 4, BED_Y - h, 8, h * 1.4);
        g.globalAlpha = 0.18 * e;
        g.drawImage(this.flameSprites[4], x - 2, BED_Y - h * 0.5, 4, h * 0.7);
      }
    }
    g.globalCompositeOperation = "source-over";
    g.globalAlpha = 1;
  }

  /* split firewood (beech), 25 cm long – about two thirds of the chamber width */
  _makeLogs() {
    let seed = 11;
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    const mk = (x, y, len, rot, h, flip, fuel) => {
      /* outline: jagged split edge below, rounder bark edge above */
      const n = 26;
      const top = [];
      const bot = [];
      for (let k = 0; k < n; k++) {
        const u = k / (n - 1);
        const xx = -len / 2 + u * len;
        const taper = 1 - 0.08 * Math.abs(u - 0.5) * 2;
        top.push([xx, -h * taper * (0.94 + 0.05 * Math.sin(u * 9 + rnd()) + rnd() * 0.03)]);
        bot.push([len / 2 - u * len, h * taper * (0.9 + rnd() * 0.12)]);
      }
      /* the split runs diagonally: bark covers the upper part */
      const ph0 = rnd() * 6;
      const barkLine = Array.from({ length: n }, (_, k) => -h * (0.18 + 0.07 * Math.sin(k * 0.23 + ph0) + rnd() * 0.04));
      /* charcoal cells (alligator pattern), shared by the charred and the glowing texture */
      const cells = [];
      for (let yy = -h; yy < h; ) {
        const rh = 1.6 + rnd() * 1.8;
        for (let xx = -len / 2 - rnd() * 3; xx < len / 2 + 2; ) {
          const cw = 2 + rnd() * 4.5;
          cells.push([xx + (rnd() - 0.5) * 0.4, yy + (rnd() - 0.5) * 0.3, cw, rh, rnd()]);
          xx += cw;
        }
        yy += rh;
      }
      return { x, y, len, rot, h, flip, fuel, top, bot, barkLine, cells, seed: Math.floor(rnd() * 1e6), ph: rnd() * 50 };
    };
    return [
      mk(97, BED_Y - 1, 96, 0.05, 10.5, false, 0),
      mk(104, BED_Y + 7, 100, -0.06, 11.5, true, 0),
      mk(100, BED_Y - 13, 90, -0.16, 9.5, false, 0.75),
    ];
  }

  /* painted once per log: fresh and charred version */
  _logTexture(l, charred) {
    const S = 5;
    const pad = 6;
    const w = Math.ceil((l.len + l.h * 1.2 + pad * 2) * S);
    const hgt = Math.ceil((l.h * 2 + pad * 2) * S);
    const c = document.createElement("canvas");
    c.width = w;
    c.height = hgt;
    const g = c.getContext("2d");
    g.scale(S, S);
    g.translate(l.len / 2 + pad, l.h + pad);
    let seed = l.seed + (charred ? 7 : 0);
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    const L = l.len;
    const h = l.h;
    const outline = () => {
      g.beginPath();
      l.top.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y)));
      l.bot.forEach(([x, y]) => g.lineTo(x, y));
      g.closePath();
    };
    g.save();
    outline();
    g.clip();

    if (!charred) {
      /* split face: pale beech wood with long fibres */
      let gr = g.createLinearGradient(0, -h, 0, h);
      gr.addColorStop(0, "#d9b98c");
      gr.addColorStop(0.55, "#c39a6b");
      gr.addColorStop(1, "#8a6343");
      g.fillStyle = gr;
      g.fillRect(-L, -h * 2, L * 2, h * 4);
      for (let k = 0; k < 140; k++) {
        const y = -h + rnd() * h * 2;
        const x0 = -L / 2 + rnd() * L * 0.7;
        const len = L * (0.15 + rnd() * 0.6);
        const tone = rnd();
        g.strokeStyle = tone > 0.5 ? `rgba(120,82,48,${0.12 + rnd() * 0.25})` : `rgba(240,215,175,${0.1 + rnd() * 0.2})`;
        g.lineWidth = 0.15 + rnd() * 0.35;
        g.beginPath();
        g.moveTo(x0, y);
        const wav = (rnd() - 0.5) * 1.6;
        g.bezierCurveTo(x0 + len * 0.33, y + wav, x0 + len * 0.66, y - wav, x0 + len, y + wav * 0.5);
        g.stroke();
      }
      /* a knot */
      const kx = (rnd() - 0.5) * L * 0.5;
      const ky = h * (0.15 + rnd() * 0.3);
      for (let r = 3.2; r > 0.4; r -= 0.7) {
        g.strokeStyle = `rgba(95,60,32,${0.25 + (3.2 - r) * 0.12})`;
        g.lineWidth = 0.35;
        g.beginPath();
        g.ellipse(kx, ky, r * 1.9, r * 0.75, 0, 0, Math.PI * 2);
        g.stroke();
      }
      g.fillStyle = "rgba(70,42,22,0.75)";
      g.beginPath();
      g.ellipse(kx, ky, 0.9, 0.5, 0, 0, Math.PI * 2);
      g.fill();
      /* bark: grey-brown beech bark on the upper part */
      g.beginPath();
      l.top.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y)));
      for (let k = l.barkLine.length - 1; k >= 0; k--) g.lineTo(l.top[k][0], l.barkLine[k]);
      g.closePath();
      gr = g.createLinearGradient(0, -h, 0, 0);
      gr.addColorStop(0, "#8a8178");
      gr.addColorStop(0.35, "#6e6359");
      gr.addColorStop(1, "#4a3f37");
      g.fillStyle = gr;
      g.fill();
      g.save();
      g.clip();
      for (let k = 0; k < 90; k++) {
        const x = -L / 2 + rnd() * L;
        const y = -h + rnd() * h;
        const len = 2 + rnd() * 9;
        g.strokeStyle = rnd() > 0.4 ? `rgba(35,28,24,${0.3 + rnd() * 0.4})` : `rgba(170,160,150,${0.2 + rnd() * 0.3})`;
        g.lineWidth = 0.2 + rnd() * 0.4;
        g.beginPath();
        g.moveTo(x, y);
        g.lineTo(x + len, y + (rnd() - 0.5) * 0.6);
        g.stroke();
      }
      /* lichen spots */
      for (let k = 0; k < 6; k++) {
        g.fillStyle = `rgba(150,160,120,${0.15 + rnd() * 0.2})`;
        g.beginPath();
        g.ellipse(-L / 2 + rnd() * L, -h * (0.5 + rnd() * 0.4), 1 + rnd() * 2.5, 0.6 + rnd(), 0, 0, Math.PI * 2);
        g.fill();
      }
      g.restore();
      /* edge where bark meets wood: a thin light cambium line */
      g.strokeStyle = "rgba(225,195,150,0.7)";
      g.lineWidth = 0.4;
      g.beginPath();
      l.barkLine.forEach((y, k) => (k ? g.lineTo(l.top[k][0], y + 0.3) : g.moveTo(l.top[k][0], y + 0.3)));
      g.stroke();
    } else {
      /* charcoal: irregular blocks separated by deep cracks, grey ash on top */
      g.fillStyle = "#050404";
      g.fillRect(-L, -h * 2, L * 2, h * 4);
      for (const [x, y, cw, rh, v] of l.cells) {
        const up = clamp((-y + h) / (h * 2));
        const base = Math.round(12 + v * 16 + up * 16);
        g.fillStyle = `rgb(${base + 4},${base + 2},${base})`;
        const j = () => (rnd() - 0.5) * 0.5;
        const gp = 0.2;
        g.beginPath();
        g.moveTo(x + gp + j(), y + gp + j());
        g.quadraticCurveTo(x + cw / 2, y + gp + j() * 0.6 - 0.15, x + cw - gp + j(), y + gp + j());
        g.lineTo(x + cw - gp + j(), y + rh - gp + j());
        g.quadraticCurveTo(x + cw / 2, y + rh - gp + 0.15, x + gp + j(), y + rh - gp + j());
        g.closePath();
        g.fill();
        /* silky sheen on the upper edge of each block */
        g.strokeStyle = `rgba(150,145,160,${0.08 + up * 0.18})`;
        g.lineWidth = 0.25;
        g.beginPath();
        g.moveTo(x + 0.5, y + 0.45);
        g.lineTo(x + cw - 0.5, y + 0.45);
        g.stroke();
      }
      for (let k = 0; k < 18; k++) {
        g.fillStyle = `rgba(190,185,178,${0.12 + rnd() * 0.2})`;
        g.beginPath();
        g.ellipse(-L / 2 + rnd() * L, -h * (0.55 + rnd() * 0.4), 1 + rnd() * 3, 0.4 + rnd() * 0.6, 0, 0, Math.PI * 2);
        g.fill();
      }
    }
    /* round shading: light from above, dark underside */
    const sh = g.createLinearGradient(0, -h, 0, h);
    sh.addColorStop(0, "rgba(255,255,255,0.10)");
    sh.addColorStop(0.45, "rgba(0,0,0,0)");
    sh.addColorStop(1, "rgba(0,0,0,0.45)");
    g.fillStyle = sh;
    g.fillRect(-L, -h * 2, L * 2, h * 4);
    g.restore();

    /* sawn end with growth rings around the pith and radial cracks */
    const ex = L / 2 - 1;
    const endPath = () => {
      g.beginPath();
      g.moveTo(ex - 2, l.top[l.top.length - 1][1]);
      g.quadraticCurveTo(ex + h * 0.62, -h * 0.55, ex + h * 0.5, h * 0.2);
      g.lineTo(ex - 1.5, l.bot[0][1]);
      g.closePath();
    };
    endPath();
    g.fillStyle = charred ? "#1e1a17" : "#dcc29a";
    g.fill();
    g.save();
    endPath();
    g.clip();
    const px = ex - 1.5;
    const py = h * 0.9;
    for (let r = 2; r < h * 2.2; r += 1.1 + rnd() * 0.8) {
      g.strokeStyle = charred ? `rgba(0,0,0,${0.5 + rnd() * 0.3})` : `rgba(150,110,70,${0.35 + rnd() * 0.35})`;
      g.lineWidth = 0.3 + rnd() * 0.3;
      g.beginPath();
      g.arc(px, py, r, -Math.PI * 0.65, -Math.PI * 0.02);
      g.stroke();
    }
    g.strokeStyle = charred ? "rgba(255,255,255,0.08)" : "rgba(80,50,28,0.6)";
    g.lineWidth = 0.4;
    for (let k = 0; k < 4; k++) {
      const a = -Math.PI * (0.15 + rnd() * 0.45);
      g.beginPath();
      g.moveTo(px, py);
      g.lineTo(px + Math.cos(a) * h * 1.6, py + Math.sin(a) * h * 1.6);
      g.stroke();
    }
    /* bark rim on the end */
    g.strokeStyle = charred ? "#2a2522" : "#5d5249";
    g.lineWidth = 1.8;
    g.beginPath();
    g.moveTo(ex - 2, l.top[l.top.length - 1][1]);
    g.quadraticCurveTo(ex + h * 0.62, -h * 0.55, ex + h * 0.5, h * 0.2);
    g.stroke();
    g.restore();

    /* splinters along the split edge */
    if (!charred) {
      g.fillStyle = "#c9a476";
      for (let k = 0; k < 4; k++) {
        const x = -L / 2 + rnd() * L;
        const y = l.bot[Math.floor(rnd() * l.bot.length)][1] * 0.95;
        g.beginPath();
        g.moveTo(x, y);
        g.lineTo(x + 4 + rnd() * 5, y + 0.4);
        g.lineTo(x + 1, y + 0.9);
        g.closePath();
        g.fill();
      }
    }
    return { canvas: c, ox: -(l.len / 2 + pad), oy: -(l.h + pad), w: w / S, h: hgt / S };
  }

  _drawLogs(g, i, fuel, mode) {
    if (!this.logs) this.logs = this._makeLogs();
    const charred = mode === "off" ? 0 : clamp(Math.max(1.1 - fuel, i > 0.05 ? 0.25 + i * 0.15 : 0));
    const t = this.t;
    for (const l of this.logs) {
      if (l.fuel && fuel < l.fuel) continue;
      if (!l.tex) {
        l.tex = this._logTexture(l, false);
        l.texC = this._logTexture(l, true);
      }
      const shrink = 0.78 + 0.22 * clamp(fuel);
      g.save();
      g.translate(l.x, l.y + l.h * (1 - shrink));
      g.rotate(l.rot);
      if (l.flip) g.scale(-1, 1);
      g.scale(0.92 + 0.08 * clamp(fuel), shrink);
      const T = l.tex;
      g.drawImage(T.canvas, T.ox, T.oy, T.w, T.h);
      if (charred > 0.01) {
        g.globalAlpha = charred;
        g.drawImage(l.texC.canvas, T.ox, T.oy, T.w, T.h);
        g.globalAlpha = 1;
      }
      /* burning: glowing underside and glowing cracks */
      if (i > 0.02 || charred > 0.3) {
        const glow = clamp(i * 1.2 + charred * 0.4) * (0.8 + 0.2 * noise1(t * 0.07 + l.ph));
        g.globalCompositeOperation = "lighter";
        const gl = g.createLinearGradient(0, -l.h, 0, l.h);
        gl.addColorStop(0, "rgba(255,90,10,0)");
        gl.addColorStop(0.6, `rgba(255,80,10,${0.1 * glow})`);
        gl.addColorStop(1, `rgba(255,140,40,${0.45 * glow})`);
        g.fillStyle = gl;
        g.beginPath();
        l.top.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y)));
        l.bot.forEach(([x, y]) => g.lineTo(x, y));
        g.closePath();
        g.fill();
        if (charred > 0.3) {
          /* ember cracks: the charcoal pattern glows from inside */
          g.globalAlpha = clamp((charred - 0.3) * 1.6) * glow * 0.9;
          g.filter = "none";
          g.drawImage(this._emberCrackTex(l), T.ox, T.oy, T.w, T.h);
          g.globalAlpha = 1;
        }
        g.globalCompositeOperation = "source-over";
      }
      g.restore();
    }
  }

  /* orange crack pattern used for glowing charcoal */
  _emberCrackTex(l) {
    if (l.crack) return l.crack;
    const T = l.tex;
    const S = 4;
    const c = document.createElement("canvas");
    c.width = Math.ceil(T.w * S);
    c.height = Math.ceil(T.h * S);
    const g = c.getContext("2d");
    g.scale(S, S);
    g.translate(-T.ox, -T.oy);
    g.beginPath();
    l.top.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y)));
    l.bot.forEach(([x, y]) => g.lineTo(x, y));
    g.closePath();
    g.clip();
    let seed = l.seed + 3;
    const rnd = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    /* light leaks out of the cracks between the charcoal blocks, stronger at the bottom */
    for (const [x, y, cw, rh, v] of l.cells) {
      if (y < -l.h * 0.3 || rnd() < 0.45) continue;
      const a = 0.35 + 0.65 * clamp((y + l.h) / (l.h * 2));
      g.strokeStyle = `rgba(255,${Math.round(100 + v * 70)},30,${a})`;
      g.lineWidth = 0.3 + v * 0.25;
      g.beginPath();
      g.moveTo(x, y + rnd() * 0.4);
      g.quadraticCurveTo(x + (rnd() - 0.5) * 0.8, y + rh / 2, x + (rnd() - 0.5) * 0.4, y + rh);
      if (v > 0.6) g.lineTo(x + cw * (0.3 + rnd() * 0.6), y + rh + (rnd() - 0.5) * 0.3);
      g.stroke();
    }
    l.crack = c;
    return c;
  }
}

/* --------------------------------------------------------- wood pile svg */

/* end view of split firewood pieces, stacked */
const woodPile = (count) => {
  const full = Math.floor(count);
  const half = count - full >= 0.5 ? 1 : 0;
  const n = full + half;
  if (n <= 0) return "";
  const shown = Math.min(n, 15);
  const r = 13;
  let rows = 1;
  while ((rows * (rows + 1)) / 2 < shown) rows++;
  const dx = r * 1.66;
  const dy = r * 0.98;
  const width = (rows - 1) * dx + r * 1.7 + 4;
  const height = rows * dy + 4;
  const wedge = (x, y, up, scale, k) => {
    /* sector of a log: apex at the centre of the trunk, bark on the arc */
    const R = r * scale;
    const a0 = (-90 - 52) * (Math.PI / 180);
    const a1 = (-90 + 52) * (Math.PI / 180);
    const p = (a, rr) => `${(Math.cos(a) * rr).toFixed(1)} ${(Math.sin(a) * rr + R * 0.62).toFixed(1)}`;
    const rings = [0.35, 0.62]
      .map((f) => `<path d="M${p(a0 + 0.12, R * f)} A${R * f} ${R * f} 0 0 1 ${p(a1 - 0.12, R * f)}" fill="none" stroke="#b5884f" stroke-width="0.9"/>`)
      .join("");
    return `<g transform="translate(${x.toFixed(1)} ${(y + (up ? 0 : R * 0.24)).toFixed(1)}) rotate(${up ? 0 : 180}) rotate(${((k * 37) % 7) - 3})">
      <path d="M0 ${(R * 0.62).toFixed(1)} L${p(a0, R)} A${R} ${R} 0 0 1 ${p(a1, R)} Z" fill="#e2c08f" stroke="#a87b48" stroke-width="0.6"/>
      ${rings}
      <path d="M${p(a0, R - 1.2)} A${R - 1.2} ${R - 1.2} 0 0 1 ${p(a1, R - 1.2)}" fill="none" stroke="#5d4031" stroke-width="2.6"/>
    </g>`;
  };
  const items = [];
  let k = 0;
  for (let row = 0; row < rows && k < shown; row++) {
    const inRow = rows - row;
    const y = height - 2 - row * dy - r * 0.62;
    const x0 = (width - (inRow - 1) * dx) / 2;
    for (let c = 0; c < inRow && k < shown; c++, k++) {
      const isHalf = half && k === shown - 1;
      items.push(wedge(x0 + c * dx, y + (isHalf ? r * 0.3 : 0), true, isHalf ? 0.68 : 1, k));
    }
  }
  const more = n > shown ? `<text x="${width + 4}" y="${height - 4}" font-size="11" fill="currentColor">+${n - shown}</text>` : "";
  return `<svg class="pile" viewBox="0 0 ${width + (more ? 26 : 0)} ${height}" style="height:${Math.max(14, height)}px">${items.join(
    ""
  )}${more}</svg>`;
};

/* ----------------------------------------------------------------- styles */

const STYLE = `
:host { display: block; }
ha-card { overflow: hidden; container-type: inline-size; height: 100%; box-sizing: border-box; }
.wrap { display: flex; gap: 16px; padding: 16px; align-items: center; }
.wrap.vertical { flex-direction: column; align-items: stretch; }
.flame-box { flex: 0 0 40%; max-width: 250px; min-width: 120px; display: flex; justify-content: center; }
.wrap.vertical .flame-box { max-width: none; flex-basis: auto; height: 240px; }
.values { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 10px; align-self: stretch; justify-content: center; }
@container (max-width: 380px) {
  .wrap:not(.horizontal) { flex-direction: column; align-items: stretch; }
  .wrap:not(.horizontal) .flame-box { max-width: none; flex-basis: auto; height: 240px; }
  .wrap:not(.horizontal) .stove { width: auto; height: 100%; }
  .wrap:not(.horizontal) .stove-img { max-width: 260px; margin: 0 auto; }
}

/* stove */
.stove { position: relative; width: 100%; aspect-ratio: 4 / 5; max-height: 320px; border-radius: 18px;
  background: linear-gradient(145deg, #3a3a3a, #1c1c1c); padding: 8px; box-sizing: border-box;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06), 0 2px 6px rgba(0,0,0,0.35); }
.wrap.vertical .stove { width: auto; height: 100%; }
.stove canvas { display: block; width: 100%; height: 100%; border-radius: 12px; background: #0b0807; }
.stove .glass { position: absolute; inset: 8px; border-radius: 12px; pointer-events: none;
  background: linear-gradient(125deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.02) 28%, rgba(255,255,255,0) 45%),
              linear-gradient(0deg, rgba(0,0,0,0.25), rgba(0,0,0,0) 12%);
  box-shadow: inset 0 0 18px rgba(0,0,0,0.8); }
.stove .door { position: absolute; inset: 4px; border-radius: 16px; border: 3px dashed #ffca28; opacity: 0; pointer-events: none; }
.dooropen .stove .door { opacity: 1; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: 0.35; } }
.stove-img { position: relative; width: 100%; }
.stove-img img { display: block; width: 100%; height: auto; }
.flame-box.has-img { height: auto !important; }
.wrap.vertical .stove-img { max-width: 260px; margin: 0 auto; }
.stove-img .win { position: absolute; overflow: hidden; background: #0b0807; }
.stove-img .win canvas { display: block; width: 100%; height: 100%; }
.stove-img .glass { position: absolute; pointer-events: none;
  background: linear-gradient(125deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.02) 28%, rgba(255,255,255,0) 45%);
  box-shadow: inset 0 0 14px rgba(0,0,0,0.8); }
.stove-img .door { position: absolute; border: 3px dashed #ffca28; opacity: 0; pointer-events: none; box-sizing: border-box; }
.dooropen .stove-img .door { opacity: 1; animation: pulse 1.2s ease-in-out infinite; }
.stove-img.debug .win { outline: 2px solid #ff1744; }
.gauge-wrap { display: flex; align-items: center; gap: 12px; }
.gauge { width: 130px; flex: 0 0 auto; }
.gauge-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.gauge-text .sub { color: var(--secondary-text-color); font-size: 0.85em; }
.spark { width: 100%; height: 70px; display: block; }
.axis { display: flex; justify-content: space-between; font-size: 0.72em; color: var(--secondary-text-color); }
.sub2 { font-size: 0.8em; color: var(--secondary-text-color); }
.tl { position: relative; height: 14px; border-radius: 4px; overflow: hidden; background: var(--divider-color, rgba(127,127,127,0.25)); }
.tl > div { position: absolute; top: 0; bottom: 0; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 10px; font-size: 0.72em; color: var(--secondary-text-color); }
.legend i { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 4px; vertical-align: 0; }
.wchart { display: flex; gap: 4px; height: 80px; align-items: stretch; }
.wb { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; min-width: 0; }
.wbar { width: 70%; min-height: 2px; border-radius: 3px 3px 0 0; background: linear-gradient(180deg, #a1887f, #6d4c41); }
.wv, .wd { font-size: 0.68em; color: var(--secondary-text-color); white-space: nowrap; }
.tring { display: flex; align-items: center; gap: 10px; }
.tring svg { width: 110px; flex: 0 0 auto; }
.tring .sub { color: var(--secondary-text-color); font-size: 0.9em; display: flex; flex-direction: column; gap: 2px; }
.flap { width: 30px; height: 21px; vertical-align: -5px; margin-right: 6px; }
.af { fill: #64b5f6; animation: af 1.5s linear infinite; }
@keyframes af { from { transform: translateX(0); } to { transform: translateX(36px); } }
.hring { position: absolute; inset: 0; pointer-events: none; }
.hring .glow { position: absolute; inset: 0; filter: drop-shadow(0 0 4px #ff6d00); }
.hring .bg, .hring .p { position: absolute; inset: 0; padding: 4px; border-radius: var(--hr, 16px); box-sizing: border-box;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); }
.hring .bg { background: rgba(255,255,255,0.12); }
.hring .p { background: conic-gradient(#ffb300 calc(var(--hp, 0) * 1turn), transparent 0); }
.pile { display: block; color: var(--secondary-text-color); }
.wood { display: flex; align-items: flex-end; gap: 10px; }
.wood.warn .val { color: #f57f17; }
/* values */
.head { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
.name { font-size: 1.15em; font-weight: 500; color: var(--primary-text-color); }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  font-size: 0.85em; font-weight: 500; color: #fff; background: var(--sc); white-space: nowrap; }
.badge .dot { width: 8px; height: 8px; border-radius: 50%; background: #fff; opacity: 0.9; }
.badge.blink .dot { animation: blink 1s steps(2, start) infinite; }
@keyframes blink { to { visibility: hidden; } }
.temp { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.temp .big { font-size: 2.4em; font-weight: 300; line-height: 1; color: var(--primary-text-color); }
.temp .big small { font-size: 0.45em; margin-left: 2px; color: var(--secondary-text-color); }
.temp .sub { color: var(--secondary-text-color); font-size: 0.9em; display: flex; flex-direction: column; gap: 2px; }
.label { color: var(--secondary-text-color); font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.04em; }
.row { display: flex; flex-direction: column; gap: 4px; }
.row .top { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.row .val { color: var(--primary-text-color); font-weight: 500; }
.bar { height: 8px; border-radius: 4px; background: var(--divider-color, rgba(127,127,127,0.25)); overflow: hidden; }
.bar > div { height: 100%; border-radius: 4px; background: var(--bc, var(--primary-color)); transition: width 1s ease; }
.steps { display: flex; gap: 4px; }
.steps button { flex: 1; height: 22px; border: 0; border-radius: 5px; padding: 0; cursor: default;
  background: var(--divider-color, rgba(127,127,127,0.25)); color: var(--secondary-text-color); font: inherit; font-size: 0.75em; }
.steps button.on { background: linear-gradient(90deg, #ffb300, #f4511e); color: #fff; }
.steps button.cur { outline: 2px solid var(--primary-text-color); outline-offset: 1px; }
.steps.ctl button { cursor: pointer; }
.steps .ends { display: flex; justify-content: space-between; font-size: 0.75em; color: var(--secondary-text-color); }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(118px, 1fr)); gap: 8px; }
.tile { background: var(--secondary-background-color, rgba(127,127,127,0.1)); border-radius: 10px; padding: 8px 10px;
  display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.tile .val { font-size: 1.05em; font-weight: 500; color: var(--primary-text-color); overflow-wrap: anywhere; }
.tile.warn { background: rgba(255, 202, 40, 0.18); }
.tile.click { cursor: pointer; }
.tile.click:hover { filter: brightness(1.08); }
.tile .val ha-icon { --mdc-icon-size: 18px; vertical-align: -3px; margin-right: 2px; }
.switch { display: inline-block; width: 30px; height: 16px; border-radius: 8px; background: var(--divider-color, #999);
  position: relative; vertical-align: -3px; margin-right: 6px; transition: background 0.2s; }
.switch::after { content: ""; position: absolute; width: 12px; height: 12px; border-radius: 50%; background: #fff; top: 2px; left: 2px; transition: left 0.2s; }
.switch.on { background: #ef6c00; }
.switch.led.on { background: var(--primary-color, #03a9f4); }
.tile input[type=range] { width: 100%; margin: 4px 0 0; accent-color: var(--primary-color, #03a9f4); }
.switch.on::after { left: 16px; }
.error { background: rgba(229, 57, 53, 0.15); color: var(--error-color, #e53935); border-radius: 10px; padding: 8px 10px; font-weight: 500;
  display: flex; gap: 8px; align-items: center; }
.missing { padding: 16px; color: var(--secondary-text-color); }
`;

/* ------------------------------------------------------------------- card */

class DrooffFireplusCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("drooff-fireplus-card-editor");
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    const hide = hideList(config);
    const show = config.show && typeof config.show === "object" ? config.show : {};
    this._config = { ...DEFAULTS, ...config };
    this._histAt = 0;
    this._hidden = new Set(hide);
    for (const [k, v] of Object.entries(show)) if (v === false) this._hidden.add(k);
    this._entities = null;
    this._built = false;
    if (this._hass) this._render();
  }

  set hass(hass) {
    const old = this._hass;
    this._hass = hass;
    /* HA hands over a new hass object on every state change anywhere; only redraw when ours changed */
    if (
      old &&
      this._built &&
      !this._sim &&
      this._entities &&
      Object.keys(this._entities).length &&
      old.locale === hass.locale &&
      old.language === hass.language &&
      old.themes === hass.themes &&
      Object.values(this._entities).every((id) => old.states[id] === hass.states[id])
    )
      return;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }

  _t() {
    return tr(this._hass, this._config);
  }

  _show(key) {
    return !this._hidden.has(key);
  }

  _resolve() {
    const r = resolveFireplus(this._hass, this._config);
    this._device = r.device;
    return r.entities;
  }

  _st(key) {
    if (this._simCache && key in this._simCache) return this._simCache[key];
    const id = this._entities && this._entities[key];
    return id ? this._hass.states[id] : undefined;
  }

  /* synthetic states while the fire simulation runs */
  _simStates() {
    const el = (performance.now() - this._sim.t0) / 1000;
    let tt = el % SIM_CYCLE;
    let ph = SIM_PHASES[0];
    for (const p of SIM_PHASES) {
      ph = p;
      if (tt < p.dur) break;
      tt -= p.dur;
    }
    const f = clamp(tt / ph.dur);
    const real = (key) => {
      const id = this._entities && this._entities[key];
      return (id && this._hass.states[id]) || { attributes: {} };
    };
    const S = (key, state, attrs = {}) => ({ state: String(state), attributes: { ...real(key).attributes, ...attrs } });
    const temp = Math.round(ph.t0 + (ph.t1 - ph.t0) * f);
    return {
      operation_status: S("operation_status", ph.status),
      temperature: S("temperature", temp, { unit_of_measurement: "°C", max_temperature: 612 }),
      target_temperature: S("target_temperature", 480, { unit_of_measurement: "°C" }),
      heating_progress: S("heating_progress", ph.status === "HEATING" ? Math.round(f * 100) : "unavailable", { unit_of_measurement: "%" }),
      air_slider_position: S("air_slider_position", ph.air, { unit_of_measurement: "%" }),
      draught: S("draught", (ph.d0 + (ph.d1 - ph.d0) * f + Math.sin(el * 1.7) * 0.8).toFixed(1), { unit_of_measurement: "Pa" }),
      weight: S("weight", ph.wood || 0, { unit_of_measurement: "kg" }),
      burn_rate: S("burn_rate", real("burn_rate").state || 3, { min: 1, max: real("burn_rate").attributes.max || 6 }),
      ember_burndown: S("ember_burndown", ph.ember ? "on" : "off"),
      error: S("error", "off"),
      door_open: S("door_open", "off"),
    };
  }

  _simStart() {
    this._sim = { t0: performance.now() };
    clearInterval(this._simTimer);
    this._simTimer = setInterval(() => {
      if (performance.now() - this._sim.t0 > SIM_CYCLE * 1000) this._simStop();
      else this._render();
    }, 1000);
    this._render();
  }

  _simStop() {
    if (!this._sim) return;
    this._sim = null;
    this._simCache = null;
    clearInterval(this._simTimer);
    window.dispatchEvent(new CustomEvent(SIM_EVENT, { detail: { on: false, done: true } }));
    this._render();
  }

  _fmt(stateObj, fallback) {
    if (!usable(stateObj)) return null;
    if (this._hass.formatEntityState) {
      try {
        return this._hass.formatEntityState(stateObj);
      } catch (e) {
        /* ignore */
      }
    }
    const u = stateObj.attributes.unit_of_measurement;
    return fallback !== undefined ? fallback : `${stateObj.state}${u ? " " + u : ""}`;
  }

  /* flame size (i), ember glow (e), scene mode and remaining fuel for the renderer */
  _intensity(status, temp) {
    const cfg = this._config;
    let i = 0;
    let e = 0;
    let mode = "fire";
    let fuel = 1;
    const hot = Number.isFinite(temp);
    if (hot) {
      i = clamp((temp - cfg.min_temperature) / (cfg.max_temperature - cfg.min_temperature));
      e = clamp((temp - 40) / 250);
    }
    switch (status) {
      case "STANDBY":
      case "UNKNOWN":
        /* oven off: cold logs, maybe some residual embers while still warm */
        i = 0;
        e = hot ? clamp((temp - 60) / 300) * 0.6 : 0;
        mode = e > 0.08 ? "ember" : "off";
        break;
      case "EMBER_PRESERVATION":
        /* air closed: dark red, slowly breathing embers, no flames */
        i = 0;
        e = 0.85;
        mode = "ember";
        break;
      case "EMBER_BURNDOWN":
        /* air open: bright glowing embers with tiny flames */
        i = Math.min(i, 0.06);
        e = 1;
        mode = "burndown";
        break;
      case "HEATING": {
        const p = num(this._st("heating_progress"));
        i = Math.max(i, Number.isFinite(p) ? clamp(0.2 + (p / 100) * 0.6) : 0.35);
        e = Math.max(e * 0.6, 0.25);
        break;
      }
      case "WOOD_REQUIRED":
        i = Math.min(i, 0.45);
        e = Math.max(e, 0.85);
        fuel = 0.5;
        break;
      case "WOOD_URGENTLY_REQUIRED":
        i = Math.min(i, 0.22);
        e = Math.max(e, 0.95);
        fuel = 0.25;
        break;
      default:
        e = Math.max(e, 0.5);
        break;
    }
    if (cfg.flame_intensity !== undefined && cfg.flame_intensity !== null) i = clamp(Number(cfg.flame_intensity));
    return { i, e, mode, fuel };
  }

  connectedCallback() {
    if (this._io && this._flameBox) this._io.observe(this._flameBox);
    if (this._fire) this._fire.attach();
    if (!this._onSim) {
      this._onSim = (ev) => {
        if (ev.detail && ev.detail.done) return;
        if (ev.detail && ev.detail.on) this._simStart();
        else this._simStop();
      };
    }
    window.addEventListener(SIM_EVENT, this._onSim);
  }

  disconnectedCallback() {
    if (this._fire) this._fire.detach();
    if (this._io) this._io.disconnect();
    window.removeEventListener(SIM_EVENT, this._onSim);
    if (this._sim) {
      this._sim = null;
      this._simCache = null;
      clearInterval(this._simTimer);
    }
  }

  /* default: open fire chamber; optional: picture of a stove with the fire inside its window */
  _stoveHtml() {
    const cfg = this._config;
    if (!cfg.stove_image) {
      return `<div class="stove"><canvas></canvas><div class="glass"></div><div class="door"></div><div class="hring"><div class="bg"></div><div class="glow"><div class="p"></div></div></div></div>`;
    }
    const w = { left: 20, top: 20, width: 60, height: 40, ...(cfg.stove_window || {}) };
    const pct = (v) => `${Number(v)}%`;
    const r = Number(cfg.stove_window_radius ?? 4);
    return `<div class="stove-img ${cfg.stove_window_debug ? "debug" : ""}">
        <img src="${esc(cfg.stove_image)}" alt="">
        <div class="win" style="left:${pct(w.left)};top:${pct(w.top)};width:${pct(w.width)};height:${pct(w.height)};border-radius:${r}px">
          <canvas></canvas><div class="glass" style="inset:0;border-radius:${r}px"></div>
        </div>
        <div class="door" style="left:${pct(w.left)};top:${pct(w.top)};width:${pct(w.width)};height:${pct(w.height)};border-radius:${r}px"></div>
        <div class="hring" style="inset:auto;left:${pct(w.left)};top:${pct(w.top)};width:${pct(w.width)};height:${pct(w.height)};--hr:${r}px"><div class="bg"></div><div class="glow"><div class="p"></div></div></div>
      </div>`;
  }

  _build() {
    this.shadowRoot || this.attachShadow({ mode: "open" });
    if (this._fire) this._fire.detach();
    if (this._io) this._io.disconnect();
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card>
        <div class="wrap">
          <div class="flame-box">${this._stoveHtml()}</div>
          <div class="values"></div>
        </div>
      </ha-card>`;
    this._wrap = this.shadowRoot.querySelector(".wrap");
    this._flameBox = this.shadowRoot.querySelector(".flame-box");
    this._flameBox.classList.toggle("has-img", !!this._config.stove_image);
    this._values = this.shadowRoot.querySelector(".values");
    this._values.addEventListener("click", (ev) => this._onClick(ev));
    this._values.addEventListener("change", (ev) => this._onChange(ev));
    this._fire = new FireRenderer(this.shadowRoot.querySelector("canvas"));
    this._fire.setWall(this._config.wall || "chamotte");
    if ("IntersectionObserver" in window) {
      this._io = new IntersectionObserver((en) => this._fire.setVisible(en.some((x) => x.isIntersecting)));
      this._io.observe(this._flameBox);
    }
    if (this.isConnected) this._fire.attach();
    this._built = true;
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (!this._built) this._build();
    if (!this._entities || Object.keys(this._entities).length === 0) this._entities = this._resolve();

    const t = this._t();
    const cfg = this._config;
    this._simCache = this._sim ? this._simStates() : null;
    if (!this._sim && !this._entities.operation_status && !this._entities.temperature) {
      this._flameBox.style.display = "none";
      this._values.innerHTML = `<div class="missing">${esc(t.not_found)}</div>`;
      return;
    }

    const statusObj = this._st("operation_status");
    const status = usable(statusObj) ? statusObj.state : "UNKNOWN";
    const tempObj = this._st("temperature");
    const temp = num(tempObj);
    const fx = this._intensity(status, temp);

    /* flame */
    this._wrap.classList.toggle("vertical", cfg.layout === "vertical");
    this._wrap.classList.toggle("horizontal", cfg.layout === "horizontal");
    this._flameBox.style.display = this._show("flame") ? "" : "none";
    if (this._show("flame")) this._fire.set(fx.i, fx.e, fx.mode, fx.fuel);
    else this._fire.set(0, 0, "off");
    const door = this._st("door_open");
    this._flameBox.classList.toggle("dooropen", !!(door && door.state === "on" && this._show("door")));
    this._updateHeatingRing(status);
    this._fetchHistory();

    /* values */
    const parts = [];
    const name =
      cfg.title !== undefined && cfg.title !== ""
        ? cfg.title
        : (this._device && this._hass.devices && this._hass.devices[this._device] &&
            (this._hass.devices[this._device].name_by_user || this._hass.devices[this._device].name)) ||
          t.title;

    const headBits = [];
    if (this._show("name")) headBits.push(`<div class="name">${esc(name)}</div>`);
    if (this._sim) headBits.push(`<div class="badge" style="--sc:#5c6bc0"><span class="dot"></span>${t.simulation}</div>`);
    if (this._show("status") && statusObj) {
      const blink = ["HEATING", "WOOD_URGENTLY_REQUIRED", "ERROR"].includes(status);
      headBits.push(
        `<div class="badge ${blink ? "blink" : ""}" style="--sc:${STATUS_COLOR[status] || STATUS_COLOR.UNKNOWN}">
           <span class="dot"></span>${esc(t.status[status] || status)}</div>`
      );
    }
    if (headBits.length) parts.push(`<div class="head">${headBits.join("")}</div>`);

    /* error */
    const errObj = this._st("error");
    if (this._show("error") && errObj && errObj.state === "on") {
      const msg = this._fmt(this._st("error_message")) || t.error;
      parts.push(`<div class="error"><ha-icon icon="mdi:alert"></ha-icon>${esc(msg)}</div>`);
    }

    /* temperature */
    if (this._show("temperature") && usable(tempObj)) {
      const sub = [];
      const tgt = num(this._st("target_temperature"));
      if (this._show("target_temperature") && Number.isFinite(tgt)) sub.push(`${t.target} ${Math.round(tgt)} °C`);
      const mx = parseFloat(tempObj.attributes.max_temperature);
      if (this._show("max_temperature") && Number.isFinite(mx)) sub.push(`${t.max} ${Math.round(mx)} °C`);
      if (this._gfx("temp_ring")) parts.push(this._tempRing(temp, tgt, mx, t, sub));
      else parts.push(`
        <div class="row">
          <span class="label">${t.temperature}</span>
          <div class="temp">
            <div class="big">${Math.round(temp)}<small>°C</small></div>
            ${sub.length ? `<div class="sub">${sub.map((s) => `<span>${esc(s)}</span>`).join("")}</div>` : ""}
          </div>
        </div>`);
    }

    /* heating progress */
    const hp = this._st("heating_progress");
    if (this._show("heating_progress") && usable(hp) && status === "HEATING") {
      const p = clamp(num(hp) / 100);
      parts.push(`
        <div class="row">
          <div class="top"><span class="label">${t.heating_progress}</span><span class="val">${Math.round(p * 100)} %</span></div>
          <div class="bar" style="--bc: linear-gradient(90deg,#ffb300,#f4511e)"><div style="width:${p * 100}%"></div></div>
        </div>`);
    }

    /* burn rate */
    const br = this._st("burn_rate");
    if (this._show("burn_rate") && usable(br)) {
      const cur = Math.round(num(br));
      const min = Math.round(parseFloat(br.attributes.min) || 1);
      const max = Math.round(parseFloat(br.attributes.max) || 6);
      const ctl = cfg.controls !== false;
      let btns = "";
      for (let s = min; s <= max; s++) {
        btns += `<button data-act="burn" data-v="${s}" class="${s <= cur ? "on" : ""} ${s === cur ? "cur" : ""}"
          ${ctl ? "" : "disabled"} title="${s}">${s}</button>`;
      }
      parts.push(`
        <div class="row">
          <div class="top"><span class="label">${t.burn_rate}</span><span class="val">${cur} / ${max}</span></div>
          <div class="steps ${ctl ? "ctl" : ""}">${btns}</div>
          <div class="steps"><div class="ends" style="flex:1"><span>${t.eco}</span><span>${t.power}</span></div></div>
        </div>`);
    }

    /* air slider */
    const air = this._st("air_slider_position");
    if (this._show("air_slider") && usable(air)) {
      const a = clamp(num(air) / 100);
      parts.push(`
        <div class="row">
          <div class="top"><span class="label">${t.air_slider}</span><span class="val">${this._gfx("air_flap") ? this._airFlap(a) : ""}${Math.round(a * 100)} %</span></div>
          <div class="bar" style="--bc: linear-gradient(90deg,#64b5f6,#1e88e5)"><div style="width:${a * 100}%"></div></div>
        </div>`);
    }

    /* tiles */
    const tiles = [];
    const dr = this._st("draught");
    let gauge = "";
    if (this._show("draught") && usable(dr)) {
      const v = num(dr);
      if (cfg.draught_display === "gauge" && Number.isFinite(v)) gauge = this._draughtGauge(v, t);
      else tiles.push(this._tile(t.draught, "mdi:weather-windy", `${Number.isFinite(v) ? v.toFixed(1) : dr.state} Pa`));
    }
    const wl = this._st("weight");
    const wood = [];
    if (this._show("wood_load") && usable(wl) && num(wl) > 0) {
      const kg = num(wl);
      const per = Number(cfg.log_weight) > 0 ? Number(cfg.log_weight) : DEFAULTS.log_weight;
      const logs = Math.max(0.5, Math.round((kg / per) * 2) / 2);
      const warn = ["WOOD_REQUIRED", "WOOD_URGENTLY_REQUIRED"].includes(status);
      const n = logs.toLocaleString(lang(this._hass, this._config));
      wood.push(`
        <div class="row">
          <div class="top"><span class="label">${t.wood_load}</span></div>
          <div class="wood ${warn ? "warn" : ""}" title="${esc(`${n} × ${per} kg`)}">
            ${this._show("wood_logs") ? woodPile(logs) : ""}
            <span class="val">${kg.toLocaleString(lang(this._hass, this._config), { minimumFractionDigits: 1, maximumFractionDigits: 1 })} kg<br><small style="color:var(--secondary-text-color);font-weight:400">≈ ${n} ${
              logs === 1 ? t.log : t.logs
            }</small></span>
          </div>
        </div>`);
    }
    if (this._show("door") && usable(door)) {
      const open = door.state === "on";
      tiles.push(this._tile(t.door, open ? "mdi:door-open" : "mdi:door-closed", open ? t.open : t.closed, open ? "warn" : ""));
    }
    const eb = this._st("ember_burndown");
    if (this._show("ember_burndown") && usable(eb)) {
      const on = eb.state === "on";
      const ctl = cfg.controls !== false;
      tiles.push(`
        <div class="tile ${ctl ? "click" : ""}" ${ctl ? 'data-act="ember"' : ""}>
          <span class="label">${t.ember}</span>
          <span class="val"><span class="switch ${on ? "on" : ""}"></span>${on ? t.ember_on : t.ember_off}</span>
        </div>`);
    }
    const ot = this._st("operating_time");
    if (this._show("operating_time") && usable(ot) && cfg.show_operating_time !== false) {
      const h = num(ot) / 3600;
      tiles.push(this._tile(t.operating_time, "mdi:history", `${Math.round(h).toLocaleString(lang(this._hass, this._config))} ${t.hours}`));
    }
    const ctl = cfg.controls !== false;
    const led = this._st("led");
    if (this._show("led") && usable(led)) {
      const on = led.state === "on";
      tiles.push(`
        <div class="tile ${ctl ? "click" : ""}" ${ctl ? 'data-act="led"' : ""}>
          <span class="label">LED</span>
          <span class="val"><span class="switch led ${on ? "on" : ""}"></span>${on ? t.on : t.off}</span>
        </div>`);
    }
    for (const [key, icon] of [["brightness", "mdi:led-strip"], ["volume", "mdi:volume-high"]]) {
      const st = this._st(key);
      if (!this._show(key) || !usable(st)) continue;
      const v = Math.round(num(st));
      const step = parseFloat(st.attributes.step) || 10;
      const icn = key === "volume" ? (v === 0 ? "mdi:volume-off" : v <= 30 ? "mdi:volume-low" : v <= 70 ? "mdi:volume-medium" : "mdi:volume-high") : icon;
      tiles.push(`
        <div class="tile">
          <span class="label">${t[key]}</span>
          <span class="val"><ha-icon icon="${icn}"></ha-icon>${v} %</span>
          ${ctl ? `<input type="range" min="${parseFloat(st.attributes.min) || 0}" max="${parseFloat(st.attributes.max) || 100}" step="${step}" value="${v}" data-range="${key}">` : ""}
        </div>`);
    }
    const eth = this._st("ethernet_link");
    const ethOn = usable(eth) && eth.state === "on";
    const wifi = this._st("wifi_signal_strength");
    if (this._show("wifi") && usable(wifi) && !ethOn) {
      const v = Math.round(num(wifi));
      const icn = v > 0 && v < 5 ? `mdi:wifi-strength-${v}` : "mdi:wifi-off";
      tiles.push(this._tile(t.wifi, icn, v > 0 && v < 5 ? `${v} / 4` : t.off));
    }
    if (this._show("ethernet") && usable(eth)) {
      tiles.push(this._tile("LAN", ethOn ? "mdi:ethernet" : "mdi:ethernet-off", ethOn ? t.connected : t.disconnected));
    }
    if (gauge) parts.push(gauge);
    parts.push(...wood);
    if (tiles.length) parts.push(`<div class="tiles">${tiles.join("")}</div>`);
    if (this._gfx("temp_history")) parts.push(this._tempHistory(t));
    if (this._gfx("timeline")) parts.push(this._timeline(t));
    if (this._gfx("wood_usage")) parts.push(this._woodUsage(t));

    const html = parts.join("");
    if (html !== this._lastHtml) {
      this._values.innerHTML = html;
      this._lastHtml = html;
    }
  }

  /* gauge from draught_max (left, overpressure) to draught_min (right, strong draught) */
  _draughtGauge(v, t) {
    const c = this._config;
    const num0 = (x, d) => (Number.isFinite(Number(x)) ? Number(x) : d);
    const max = num0(c.draught_max, DEFAULTS.draught_max);
    const min = num0(c.draught_min, DEFAULTS.draught_min) < max ? num0(c.draught_min, DEFAULTS.draught_min) : max - 1;
    const o1 = num0(c.draught_optimal_from, DEFAULTS.draught_optimal_from);
    const o2 = num0(c.draught_optimal_to, DEFAULTS.draught_optimal_to);
    const hi = Math.min(0, Math.max(o1, o2)); /* weak end of the optimum, e.g. -12 */
    const lo = Math.min(o1, o2); /* strong end of the optimum, e.g. -20 */
    const R = 50;
    const CX = 60;
    const CY = 58;
    const ang = (x) => Math.PI * clamp((x - min) / (max - min));
    const pt = (x, r = R) => [CX + Math.cos(ang(x)) * r, CY - Math.sin(ang(x)) * r];
    const arc = (a, b, color, w = 9) => {
      a = Math.max(min, a);
      b = Math.min(max, b);
      if (b <= a) return "";
      const [x0, y0] = pt(b);
      const [x1, y1] = pt(a);
      return `<path d="M${x0.toFixed(2)} ${y0.toFixed(2)} A${R} ${R} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}" stroke="${color}" stroke-width="${w}" fill="none"/>`;
    };
    const C_OVER = "#e53935";
    const C_WEAK = "#9e9e9e";
    const C_OPT = "#2e7d32";
    const C_OK = "#9ccc65";
    const zone = v > 0 ? "over" : v > hi ? "weak" : v >= lo ? "opt" : "ok";
    const col = { over: C_OVER, weak: "var(--secondary-text-color)", opt: C_OPT, ok: "#7cb342" }[zone];
    const status = { over: t.draught_negative, weak: t.draught_low, opt: t.draught_ok, ok: t.draught_high }[zone];
    const [nx, ny] = pt(clamp(v, min, max), R - 14);
    const fmt = (x) => x.toLocaleString(lang(this._hass, this._config), { maximumFractionDigits: 1, signDisplay: "exceptZero" });
    const ticks = [max, 0, hi, lo, min]
      .filter((x, i, a) => x >= min && x <= max && a.indexOf(x) === i)
      .map((x) => {
        const [a, b] = pt(x, R + 6);
        const [c2, d] = pt(x, R - 6);
        const [tx, ty] = pt(x, R + 12);
        const edge = x === min || x === max;
        return `<line x1="${a.toFixed(2)}" y1="${b.toFixed(2)}" x2="${c2.toFixed(2)}" y2="${d.toFixed(2)}" stroke="var(--secondary-text-color)" stroke-width="1"/>${
          edge ? "" : `<text x="${tx.toFixed(2)}" y="${(ty + 2).toFixed(2)}" font-size="6" text-anchor="middle" fill="var(--secondary-text-color)">${fmt(x)}</text>`
        }`;
      })
      .join("");
    return `
      <div class="row gauge-row">
        <div class="top"><span class="label">${t.draught}</span></div>
        <div class="gauge-wrap">
          <svg class="gauge" viewBox="0 -8 120 78">
            ${arc(min, max, "var(--divider-color, rgba(127,127,127,0.3))")}
            ${arc(0, max, C_OVER)}
            ${arc(hi, 0, C_WEAK)}
            ${arc(lo, hi, C_OPT)}
            ${arc(min, lo, C_OK)}
            ${ticks}
            <line x1="${CX}" y1="${CY}" x2="${nx.toFixed(2)}" y2="${ny.toFixed(2)}" stroke="var(--primary-text-color)" stroke-width="2.4" stroke-linecap="round" style="transition: all 1s"/>
            <circle cx="${CX}" cy="${CY}" r="4" fill="var(--primary-text-color)"/>
            <text x="${CX - R}" y="69" font-size="7" text-anchor="middle" fill="var(--secondary-text-color)">${fmt(max)}</text>
            <text x="${CX + R}" y="69" font-size="7" text-anchor="middle" fill="var(--secondary-text-color)">${fmt(min)}</text>
          </svg>
          <div class="gauge-text">
            <div class="val" style="font-size:1.6em;font-weight:400;color:${col}">${fmt(v)} <small style="font-size:0.55em;color:var(--secondary-text-color)">Pa</small></div>
            <div class="sub">${esc(status)}</div>
            <div class="sub">${t.draught_target} <span style="white-space:nowrap">${fmt(hi)} … ${fmt(lo)} Pa</span></div>
          </div>
        </div>
      </div>`;
  }

  /* ------------------------------------------------ optional graphics */

  _gfx(key) {
    return Array.isArray(this._config.graphics) && this._config.graphics.includes(key);
  }

  /* history of temperature, target and status (and wood load) from the recorder */
  async _fetchHistory(force = false) {
    const needs = ["temp_history", "timeline", "wood_usage"].some((k) => this._gfx(k));
    if (!needs || !this._hass || !this._hass.callWS || !this._entities) return;
    const now = Date.now();
    if (!force && this._histAt && now - this._histAt < 5 * 60 * 1000) return;
    if (this._histBusy) return;
    this._histAt = now;
    this._histBusy = true;
    const cfg = this._config;
    const hours = Math.max(1, Number(cfg.history_hours) || 6);
    const days = Math.max(1, Number(cfg.wood_days) || 7);
    const span = Math.max(hours, this._gfx("wood_usage") ? days * 24 : 0);
    const ids = ["temperature", "target_temperature", "operation_status", "weight"]
      .map((k) => this._entities[k])
      .filter(Boolean);
    try {
      const res = await this._hass.callWS({
        type: "history/history_during_period",
        start_time: new Date(now - span * 3600 * 1000).toISOString(),
        end_time: new Date(now).toISOString(),
        entity_ids: ids,
        minimal_response: true,
        no_attributes: true,
        significant_changes_only: false,
      });
      const series = (key) => {
        const id = this._entities[key];
        const rows = (res && id && res[id]) || [];
        return rows
          .map((r) => {
            const s = r.s !== undefined ? r.s : r.state;
            const t = r.lu !== undefined ? r.lu * 1000 : Date.parse(r.last_updated || r.last_changed);
            return [t, s];
          })
          .filter(([t]) => Number.isFinite(t))
          .sort((a, b) => a[0] - b[0]);
      };
      this._hist = {
        at: now,
        temp: series("temperature"),
        target: series("target_temperature"),
        status: series("operation_status"),
        weight: series("weight"),
      };
    } catch (e) {
      this._hist = { at: now, error: true, temp: [], target: [], status: [], weight: [] };
    }
    this._histBusy = false;
    this._lastHtml = null;
    this._render();
  }

  _timeLabel(h) {
    return h >= 1 ? `−${h} h` : `−${Math.round(h * 60)} min`;
  }

  /* line chart of the chamber temperature with the target as dashed line */
  _tempHistory(t) {
    const h = this._hist;
    const cfg = this._config;
    const hours = Math.max(1, Number(cfg.history_hours) || 6);
    const now = Date.now();
    const t0 = now - hours * 3600 * 1000;
    const W = 300;
    const H = 70;
    const pts = (h ? h.temp : []).map(([x, v]) => [x, parseFloat(v)]).filter(([, v]) => Number.isFinite(v));
    const cur = num(this._st("temperature"));
    if (Number.isFinite(cur)) pts.push([now, cur]);
    /* value at the start of the window */
    const inWin = pts.filter(([x]) => x >= t0);
    const before = pts.filter(([x]) => x < t0).pop();
    if (before) inWin.unshift([t0, before[1]]);
    if (inWin.length < 2) return `<div class="row"><span class="label">${t.temp_history}</span><div class="sub" style="color:var(--secondary-text-color);font-size:0.85em">${t.no_history}</div></div>`;
    const tg = (h ? h.target : []).map(([x, v]) => [x, parseFloat(v)]).filter(([, v]) => Number.isFinite(v));
    const vmax = Math.max(100, ...inWin.map(([, v]) => v), ...tg.map(([, v]) => v)) * 1.08;
    const X = (x) => ((x - t0) / (now - t0)) * W;
    const Y = (v) => H - 4 - (v / vmax) * (H - 10);
    let d = "";
    inWin.forEach(([x, v], k) => {
      d += `${k ? " L" : "M"}${X(Math.max(x, t0)).toFixed(1)} ${Y(v).toFixed(1)}`;
    });
    const area = `${d} V${H} H0 Z`;
    let target = "";
    const tgt = num(this._st("target_temperature"));
    if (Number.isFinite(tgt)) target = `<line x1="0" x2="${W}" y1="${Y(tgt).toFixed(1)}" y2="${Y(tgt).toFixed(1)}" stroke="#43a047" stroke-width="1" stroke-dasharray="4 3"/>`;
    const peak = Math.max(...inWin.map(([, v]) => v));
    return `
      <div class="row">
        <div class="top"><span class="label">${t.temp_history}</span><span class="sub2">${t.max} ${Math.round(peak)} °C</span></div>
        <svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
          <defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#ff7043" stop-opacity="0.55"/><stop offset="1" stop-color="#ff7043" stop-opacity="0"/>
          </linearGradient></defs>
          <path d="${area}" fill="url(#tg)"/>
          ${target}
          <path d="${d}" fill="none" stroke="#ff7043" stroke-width="1.8" vector-effect="non-scaling-stroke"/>
        </svg>
        <div class="axis"><span>${this._timeLabel(hours)}</span><span>${t.now}</span></div>
      </div>`;
  }

  /* coloured band of the operation states */
  _timeline(t) {
    const h = this._hist;
    const hours = Math.max(1, Number(this._config.history_hours) || 6);
    const now = Date.now();
    const t0 = now - hours * 3600 * 1000;
    const st = h ? [...h.status] : [];
    const curS = this._st("operation_status");
    if (usable(curS)) st.push([now, curS.state]);
    const before = st.filter(([x]) => x < t0).pop();
    const win = st.filter(([x]) => x >= t0);
    if (before) win.unshift([t0, before[1]]);
    if (win.length < 1) return "";
    const segs = [];
    const used = new Set();
    for (let k = 0; k < win.length; k++) {
      const [x, s] = win[k];
      const x1 = k + 1 < win.length ? win[k + 1][0] : now;
      if (x1 <= x) continue;
      used.add(s);
      const l = ((x - t0) / (now - t0)) * 100;
      const w = ((x1 - x) / (now - t0)) * 100;
      segs.push(`<div style="left:${l.toFixed(2)}%;width:${w.toFixed(2)}%;background:${STATUS_COLOR[s] || STATUS_COLOR.UNKNOWN}" title="${esc(t.status[s] || s)}"></div>`);
    }
    const legend = [...used]
      .filter((s) => s !== "UNKNOWN")
      .map((s) => `<span><i style="background:${STATUS_COLOR[s] || STATUS_COLOR.UNKNOWN}"></i>${esc(t.status[s] || s)}</span>`)
      .join("");
    return `
      <div class="row">
        <span class="label">${t.timeline}</span>
        <div class="tl">${segs.join("")}</div>
        <div class="axis"><span>${this._timeLabel(hours)}</span><span>${t.now}</span></div>
        <div class="legend">${legend}</div>
      </div>`;
  }

  /* estimated wood per day: every (re)start of burning counts as one load */
  _woodUsage(t) {
    const h = this._hist;
    const cfg = this._config;
    const days = Math.max(1, Number(cfg.wood_days) || 7);
    const perLoad = Number(cfg.wood_per_load) > 0 ? Number(cfg.wood_per_load) : 2;
    const L = lang(this._hass, cfg);
    const st = h ? h.status : [];
    const wt = h ? h.weight.map(([x, v]) => [x, parseFloat(v)]).filter(([, v]) => v > 0) : [];
    const burning = new Set(["HEATING", "REGULAR"]);
    const day0 = new Date();
    day0.setHours(0, 0, 0, 0);
    const buckets = Array.from({ length: days }, (_, k) => {
      const d = new Date(day0);
      d.setDate(d.getDate() - (days - 1 - k));
      return { start: d.getTime(), kg: 0, loads: 0 };
    });
    let prev = null;
    for (const [x, s] of st) {
      if (prev !== null && burning.has(s) && !burning.has(prev)) {
        const w = wt.filter(([wx]) => wx <= x).pop();
        const kg = w ? w[1] : perLoad;
        for (let k = buckets.length - 1; k >= 0; k--) {
          if (x >= buckets[k].start) {
            buckets[k].kg += kg;
            buckets[k].loads += 1;
            break;
          }
        }
      }
      prev = s;
    }
    const max = Math.max(1, ...buckets.map((b) => b.kg));
    const fmt = (v) => v.toLocaleString(L, { maximumFractionDigits: 1 });
    const total = buckets.reduce((a, b) => a + b.kg, 0);
    const bars = buckets
      .map((b) => {
        const day = new Date(b.start).toLocaleDateString(L, { weekday: "short" });
        return `<div class="wb" title="${b.loads} × ">
          <span class="wv">${b.kg ? fmt(b.kg) : ""}</span>
          <div class="wbar" style="height:${((b.kg / max) * 100).toFixed(1)}%"></div>
          <span class="wd">${esc(day)}</span></div>`;
      })
      .join("");
    return `
      <div class="row">
        <div class="top"><span class="label">${t.wood_usage}</span><span class="sub2">Σ ${fmt(total)} kg</span></div>
        <div class="wchart">${bars}</div>
      </div>`;
  }

  /* temperature as ring with target and max markers */
  _tempRing(temp, tgt, mx, t, sub) {
    const scaleMax = Math.max(700, Number.isFinite(mx) ? mx * 1.1 : 0, Number(this._config.max_temperature) * 1.15 || 0);
    const R = 40;
    const C = 50;
    const a0 = 135;
    const sweep = 270;
    const pt = (v, r = R) => {
      const a = ((a0 + sweep * clamp(v / scaleMax)) * Math.PI) / 180;
      return [C + Math.cos(a) * r, C + Math.sin(a) * r];
    };
    const arc = (v0, v1, col, w) => {
      const [x0, y0] = pt(v0);
      const [x1, y1] = pt(v1);
      const large = sweep * (clamp(v1 / scaleMax) - clamp(v0 / scaleMax)) > 180 ? 1 : 0;
      return `<path d="M${x0.toFixed(2)} ${y0.toFixed(2)} A${R} ${R} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}" stroke="${col}" stroke-width="${w}" fill="none" stroke-linecap="round"/>`;
    };
    const mark = (v, col) => {
      if (!Number.isFinite(v)) return "";
      const [x0, y0] = pt(v, R - 9);
      const [x1, y1] = pt(v, R + 9);
      return `<line x1="${x0.toFixed(2)}" y1="${y0.toFixed(2)}" x2="${x1.toFixed(2)}" y2="${y1.toFixed(2)}" stroke="${col}" stroke-width="2.2" stroke-linecap="round"/>`;
    };
    const v = Number.isFinite(temp) ? temp : 0;
    return `
      <div class="row">
        <span class="label">${t.temperature}</span>
        <div class="tring">
          <svg viewBox="0 0 100 92">
            <defs><linearGradient id="trg" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0" stop-color="#ffb300"/><stop offset="0.6" stop-color="#f4511e"/><stop offset="1" stop-color="#b71c1c"/>
            </linearGradient></defs>
            ${arc(0, scaleMax, "var(--divider-color, rgba(127,127,127,0.3))", 8)}
            ${v > 0 ? arc(0, Math.max(v, scaleMax * 0.01), "url(#trg)", 8) : ""}
            ${this._show("target_temperature") ? mark(tgt, "#43a047") : ""}
            ${this._show("max_temperature") ? mark(mx, "var(--secondary-text-color)") : ""}
            <text x="50" y="54" text-anchor="middle" font-size="20" fill="var(--primary-text-color)">${Math.round(v)}</text>
            <text x="50" y="68" text-anchor="middle" font-size="8" fill="var(--secondary-text-color)">°C</text>
          </svg>
          ${sub.length ? `<div class="sub">${sub.map((s) => `<span>${esc(s)}</span>`).join("")}</div>` : ""}
        </div>
      </div>`;
  }

  /* air slider as a damper flap; the air flows faster the wider it is open */
  _airFlap(a) {
    const ang = -90 + 90 * a;
    const dur = a > 0.02 ? (2.2 - 1.6 * a).toFixed(2) : 0;
    const flow =
      a > 0.02
        ? [8, 14, 20]
            .map(
              (y, k) =>
                `<circle class="af" cx="2" cy="${y}" r="1.4" style="animation-duration:${dur}s;animation-delay:-${(k * dur) / 3}s;opacity:${(0.4 + 0.6 * a).toFixed(2)}"/>`
            )
            .join("")
        : "";
    return `<svg class="flap" viewBox="0 0 40 28">
      <rect x="1" y="3" width="38" height="22" rx="4" fill="none" stroke="var(--secondary-text-color)" stroke-width="1.4"/>
      ${flow}
      <g transform="translate(20 14) rotate(${ang.toFixed(1)})">
        <rect x="-1.6" y="-10" width="3.2" height="20" rx="1.4" fill="#1e88e5"/>
      </g>
      <circle cx="20" cy="14" r="1.8" fill="var(--primary-text-color)"/>
    </svg>`;
  }

  /* progress ring around the window while heating up */
  _updateHeatingRing(status) {
    const ring = this._flameBox && this._flameBox.querySelector(".hring");
    if (!ring) return;
    const hp = this._st("heating_progress");
    const on = this._gfx("heating_ring") && status === "HEATING" && usable(hp);
    ring.style.display = on ? "" : "none";
    if (on) ring.style.setProperty("--hp", clamp(num(hp) / 100).toFixed(3));
  }

  _tile(label, icon, value, cls = "") {
    return `<div class="tile ${cls}"><span class="label">${esc(label)}</span>
      <span class="val"><ha-icon icon="${icon}"></ha-icon>${esc(value)}</span></div>`;
  }

  _onClick(ev) {
    const el = ev.target.closest("[data-act]");
    if (!el || this._config.controls === false) return;
    if (el.dataset.act === "burn") {
      this._hass.callService("number", "set_value", {
        entity_id: this._entities.burn_rate,
        value: Number(el.dataset.v),
      });
    } else if (el.dataset.act === "ember") {
      this._hass.callService("switch", "toggle", { entity_id: this._entities.ember_burndown });
    } else if (el.dataset.act === "led") {
      this._hass.callService("switch", "toggle", { entity_id: this._entities.led });
    }
  }

  _onChange(ev) {
    const el = ev.target.closest("[data-range]");
    if (!el || this._config.controls === false) return;
    this._hass.callService("number", "set_value", { entity_id: this._entities[el.dataset.range], value: Number(el.value) });
  }
}

/* ------------------------------------------------- stove picture (editor) */

const DEFAULT_WINDOW = { left: 20, top: 20, width: 60, height: 40 };

/* Drooff stoves that can be equipped with fire+ (all wood stoves except APRICA 2 Cook and FARINI).
   [id, name, output kW, minimum draught Pa, product page slug if known].
   Source: Drooff catalogue / technical information; above 20 Pa a draught limiter is required. */
const DROOFF_BASE = "https://www.drooff-kaminofen.de/drooff/de/";
const DRAUGHT_LIMIT = 20;
const STOVE_MODELS = [
  ["andalo3s", "ANDALO 3 S", "3–6", 12],
  ["andalo3m", "ANDALO 3 M", "3–6", 12],
  ["andalo3l", "ANDALO 3 L", "3–6", 12],
  ["aprica2", "APRICA 2 / Trend / Plus / Edition", "3–6", 12],
  ["arola", "AROLA / Edition", "4–8", 12, "arola.html"],
  ["brunello2s", "BRUNELLO 2 S", "3–6", 12],
  ["brunello2m", "BRUNELLO 2 M", "3–6", 12],
  ["brunello2l", "BRUNELLO 2 L / Groove", "3–6", 12, "brunello-2-l.html"],
  ["catania", "CATANIA", "3–6", 12],
  ["forano", "FORANO", "3–6", 12, "forano.html"],
  ["garda", "GARDA / Plus", "4–8", 12],
  ["imola", "IMOLA / SP", "4–8", 12],
  ["livera2m", "LIVERA 2 M", "3–6", 12],
  ["livera2l", "LIVERA 2 L", "3–6", 12],
  ["liverapm", "LIVERA Panorama M", "5–8", 12],
  ["liverapl", "LIVERA Panorama L", "5–8", 12],
  ["varese3", "VARESE 3", "3–6", 12],
  ["varese3w", "VARESE 3 W", "7.9–10.5", 12],
].map(([id, name, kw, pa, slug]) => ({ id, name, kw, pa, url: DROOFF_BASE + (slug || "kaminofen") }));

const loadImageFile = (file) =>
  new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("image"));
    };
    img.src = url;
  });

/* find the glass window: the largest dark area (black frame + dark glass) */
const detectWindow = (data, w, h) => {
  const N = w * h;
  const dark = new Uint8Array(N);
  for (let k = 0; k < N; k++) {
    const o = k * 4;
    dark[k] = data[o + 3] > 128 && (data[o] + data[o + 1] + data[o + 2]) / 3 < 60 ? 1 : 0;
  }
  const label = new Int32Array(N);
  const stack = new Int32Array(N);
  let best = 0;
  let bestSize = 0;
  let next = 0;
  for (let k = 0; k < N; k++) {
    if (!dark[k] || label[k]) continue;
    next++;
    let sp = 0;
    let size = 0;
    stack[sp++] = k;
    label[k] = next;
    while (sp) {
      const q = stack[--sp];
      size++;
      const x = q % w;
      const nb = [x > 0 ? q - 1 : -1, x < w - 1 ? q + 1 : -1, q - w, q + w];
      for (const n of nb) {
        if (n >= 0 && n < N && dark[n] && !label[n]) {
          label[n] = next;
          stack[sp++] = n;
        }
      }
    }
    if (size > bestSize) {
      bestSize = size;
      best = next;
    }
  }
  if (!best || bestSize < N * 0.01) return { ...DEFAULT_WINDOW, found: false };

  let x0 = w;
  let x1 = 0;
  let y0 = h;
  let y1 = 0;
  for (let k = 0; k < N; k++) {
    if (label[k] !== best) continue;
    const x = k % w;
    const y = (k - x) / w;
    if (x < x0) x0 = x;
    if (x > x1) x1 = x;
    if (y < y0) y0 = y;
    if (y > y1) y1 = y;
  }
  const inC = (x, y) => label[y * w + x] === best;
  /* drop thin parts at the sides (e.g. a door handle) */
  const runs = [];
  let start = -1;
  for (let x = x0; x <= x1 + 1; x++) {
    let cnt = 0;
    if (x <= x1) for (let y = y0; y <= y1; y++) cnt += inC(x, y) ? 1 : 0;
    const on = x <= x1 && cnt / (y1 - y0 + 1) > 0.15;
    if (on && start < 0) start = x;
    if (!on && start >= 0) {
      runs.push([start, x - 1]);
      start = -1;
    }
  }
  const keep = runs.filter(([a, b]) => b - a + 1 >= 0.08 * (x1 - x0 + 1));
  if (keep.length) {
    x0 = keep[0][0];
    x1 = keep[keep.length - 1][1];
  }
  let ry0 = -1;
  let ry1 = -1;
  for (let y = y0; y <= y1; y++) {
    let cnt = 0;
    for (let x = x0; x <= x1; x++) cnt += inC(x, y) ? 1 : 0;
    if (cnt / (x1 - x0 + 1) > 0.1) {
      if (ry0 < 0) ry0 = y;
      ry1 = y;
    }
  }
  if (ry0 >= 0) {
    y0 = ry0;
    y1 = ry1;
  }
  /* step inside the black frame */
  const bw = x1 - x0 + 1;
  const bh = y1 - y0 + 1;
  const scan = (x, y, dx, dy, cap) => {
    let k = 0;
    while (k < cap && x + dx * k >= 0 && x + dx * k < w && y + dy * k >= 0 && y + dy * k < h && dark[(y + dy * k) * w + x + dx * k]) k++;
    return Math.max(k, Math.round(cap * 0.15));
  };
  const my = Math.round((y0 + y1) / 2);
  const mx = Math.round((x0 + x1) / 2);
  const capX = Math.round(bw * 0.12);
  const capY = Math.round(bh * 0.12);
  const l = scan(x0, my, 1, 0, capX);
  const r = scan(x1, my, -1, 0, capX);
  const t = scan(mx, y0, 0, 1, capY);
  const b = scan(mx, y1, 0, -1, capY);
  const round1 = (v) => Math.round(v * 10) / 10;
  return {
    left: round1(((x0 + l) / w) * 100),
    top: round1(((y0 + t) / h) * 100),
    width: round1(((bw - l - r) / w) * 100),
    height: round1(((bh - t - b) / h) * 100),
    found: true,
  };
};

/* scale down, make a white background transparent, crop to the stove, find its window */
const processStoveImage = async (file) => {
  const img = await loadImageFile(file);
  const sc = Math.min(1, 640 / img.naturalHeight, 900 / img.naturalWidth);
  const w = Math.max(1, Math.round(img.naturalWidth * sc));
  const h = Math.max(1, Math.round(img.naturalHeight * sc));
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const g = c.getContext("2d");
  g.drawImage(img, 0, 0, w, h);
  const id = g.getImageData(0, 0, w, h);
  const p = id.data;
  const N = w * h;
  const isBg = (k) => {
    const o = k * 4;
    if (p[o + 3] < 20) return true;
    const mn = Math.min(p[o], p[o + 1], p[o + 2]);
    const mx = Math.max(p[o], p[o + 1], p[o + 2]);
    return mn > 232 && mx - mn < 16;
  };
  /* flood fill the background from the border */
  const bg = new Uint8Array(N);
  const stack = new Int32Array(N);
  let sp = 0;
  const push = (k) => {
    if (!bg[k] && isBg(k)) {
      bg[k] = 1;
      stack[sp++] = k;
    }
  };
  for (let x = 0; x < w; x++) {
    push(x);
    push((h - 1) * w + x);
  }
  for (let y = 0; y < h; y++) {
    push(y * w);
    push(y * w + w - 1);
  }
  while (sp) {
    const q = stack[--sp];
    const x = q % w;
    if (x > 0) push(q - 1);
    if (x < w - 1) push(q + 1);
    if (q >= w) push(q - w);
    if (q < N - w) push(q + w);
  }
  let x0 = w;
  let x1 = -1;
  let y0 = h;
  let y1 = -1;
  for (let k = 0; k < N; k++) {
    if (bg[k]) {
      p[k * 4 + 3] = 0;
      continue;
    }
    const x = k % w;
    const y = (k - x) / w;
    if (x < x0) x0 = x;
    if (x > x1) x1 = x;
    if (y < y0) y0 = y;
    if (y > y1) y1 = y;
  }
  if (x1 < 0) {
    x0 = 0;
    y0 = 0;
    x1 = w - 1;
    y1 = h - 1;
  }
  g.putImageData(id, 0, 0);
  const m = 2;
  x0 = Math.max(0, x0 - m);
  y0 = Math.max(0, y0 - m);
  x1 = Math.min(w - 1, x1 + m);
  y1 = Math.min(h - 1, y1 + m);
  const cw = x1 - x0 + 1;
  const ch = y1 - y0 + 1;
  const out = document.createElement("canvas");
  out.width = cw;
  out.height = ch;
  const og = out.getContext("2d");
  og.drawImage(c, x0, y0, cw, ch, 0, 0, cw, ch);
  const win = detectWindow(og.getImageData(0, 0, cw, ch).data, cw, ch);
  let dataUrl = out.toDataURL("image/webp", 0.86);
  if (!dataUrl.startsWith("data:image/webp")) dataUrl = out.toDataURL("image/png");
  return { dataUrl, window: win, width: cw, height: ch };
};

/* ----------------------------------------------------------------- editor */

class DrooffFireplusCardEditor extends HTMLElement {
  disconnectedCallback() {
    if (this._simOn) window.dispatchEvent(new CustomEvent(SIM_EVENT, { detail: { on: false } }));
    this._simOn = false;
    if (this._onSimDone) window.removeEventListener(SIM_EVENT, this._onSimDone);
    this._onSimDone = null;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first || !this._form) this._render();
    else this._form.hass = hass;
  }

  /* elements this fire+ actually provides */
  _detect() {
    const r = resolveFireplus(this._hass, this._config);
    const available = HIDEABLE.filter((k) => !NEEDS[k] || r.entities[NEEDS[k]]);
    return { ...r, available };
  }

  _schema(det) {
    const L = lang(this._hass, this._config);
    const t = tr(this._hass, this._config);
    const entityLabel = (key) => {
      const hk = Object.keys(NEEDS).find((k) => NEEDS[k] === key);
      return (hk && t.hide_labels[hk]) || key;
    };
    this._entityLabels = Object.fromEntries(Object.keys(KEYS).map((k) => [k, entityLabel(k)]));
    return [
      { name: "title", selector: { text: {} } },
      {
        name: "language",
        selector: {
          select: {
            mode: "dropdown",
            options: [
              { value: "auto", label: t.editor.lang_auto },
              ...Object.entries(LANG_NAMES).map(([value, label]) => ({ value, label })),
            ],
            custom_value: true,
          },
        },
      },
      { name: "device", selector: { device: { integration: DOMAIN } } },
      {
        name: "wall",
        selector: {
          select: { mode: "dropdown", options: Object.entries(t.walls).map(([value, label]) => ({ value, label })) },
        },
      },
      {
        name: "show",
        selector: {
          select: {
            multiple: true,
            mode: "list",
            options: det.available.map((k) => ({ value: k, label: t.hide_labels[k] })),
          },
        },
      },
      {
        type: "grid",
        name: "",
        schema: [
          { name: "min_temperature", selector: { number: { min: 0, max: 500, step: 10, mode: "box", unit_of_measurement: "°C" } } },
          { name: "max_temperature", selector: { number: { min: 100, max: 1000, step: 10, mode: "box", unit_of_measurement: "°C" } } },
        ],
      },
      { name: "log_weight", selector: { number: { min: 0.1, max: 5, step: 0.05, mode: "box", unit_of_measurement: "kg" } } },
      { name: "controls", selector: { boolean: {} } },
      {
        name: "graphics",
        selector: {
          select: { multiple: true, mode: "list", options: GRAPHICS.map((k) => ({ value: k, label: t.graphics_labels[k] })) },
        },
      },
      {
        type: "grid",
        name: "",
        schema: [
          { name: "history_hours", selector: { number: { min: 1, max: 48, step: 1, mode: "box", unit_of_measurement: "h" } } },
          { name: "wood_days", selector: { number: { min: 1, max: 31, step: 1, mode: "box" } } },
          { name: "wood_per_load", selector: { number: { min: 0.5, max: 10, step: 0.1, mode: "box", unit_of_measurement: "kg" } } },
        ],
      },
      {
        name: "draught_display",
        selector: {
          select: {
            mode: "dropdown",
            options: [
              { value: "tile", label: t.editor.draught_tile },
              { value: "gauge", label: t.editor.draught_gauge },
            ],
          },
        },
      },
      {
        type: "expandable",
        name: "advanced",
        flatten: true,
        title: t.editor.advanced,
        schema: [
          {
            type: "grid",
            name: "",
            schema: [
              ["draught_min", -100, 0, 1],
              ["draught_max", 0, 50, 1],
              ["draught_optimal_from", -100, 0, 0.5],
              ["draught_optimal_to", -100, 0, 0.5],
            ].map(([name, min, max, step]) => ({ name, selector: { number: { min, max, step, mode: "box" } } })),
          },
        ],
      },
      {
        name: "layout",
        selector: {
          select: {
            mode: "dropdown",
            options: [
              { value: "auto", label: "Auto" },
              { value: "horizontal", label: t.editor.layout_horizontal },
              { value: "vertical", label: t.editor.layout_vertical },
            ],
          },
        },
      },
      ...(this._config.stove_image
        ? [
            {
              type: "expandable",
              name: "stove_window",
              title: t.editor.stove_window,
              schema: [
                {
                  type: "grid",
                  name: "",
                  schema: ["left", "top", "width", "height"].map((k) => ({
                    name: k,
                    selector: { number: { min: 0, max: 100, step: 0.1, mode: "box", unit_of_measurement: "%" } },
                  })),
                },
                { name: "stove_window_radius", selector: { number: { min: 0, max: 60, step: 1, mode: "box", unit_of_measurement: "px" } } },
              ],
            },
            { name: "stove_window_debug", selector: { boolean: {} } },
          ]
        : []),
      {
        type: "expandable",
        name: "advanced_language",
        flatten: true,
        title: t.editor.advanced_language,
        schema: [{ name: "translations", selector: { object: {} } }],
      },
      {
        type: "expandable",
        name: "entities",
        title: t.editor.entities,
        schema: Object.entries(KEYS).map(([k, def]) => ({ name: k, selector: { entity: { domain: def.domain } } })),
      },
    ];
  }

  _render() {
    if (!this._hass || !this._config) return;
    const det = this._detect();
    this._det = det;
    this._renderPicker();
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (sch) =>
        tr(this._hass, this._config).editor[sch.name] || (this._entityLabels && this._entityLabels[sch.name]) || sch.name;
      this._form.addEventListener("value-changed", (ev) => this._changed(ev.detail.value));
      this.appendChild(this._form);
      const ver = document.createElement("div");
      ver.className = "dfp-version";
      ver.style.cssText = "margin-top:16px;font-size:0.85em;color:var(--secondary-text-color);text-align:right";
      ver.textContent = `Drooff fire+ Card v${CARD_VERSION}`;
      this.appendChild(ver);
    }
    const hide = hideList(this._config);
    this._form.hass = this._hass;
    this._form.schema = this._schema(det);
    this._form.data = {
      ...DEFAULTS,
      ...this._config,
      device: this._config.device || det.device,
      stove_window: {
        ...DEFAULT_WINDOW,
        ...(this._config.stove_window || {}),
        stove_window_radius: this._config.stove_window_radius ?? 4,
      },
      /* everything the fire+ provides is preselected unless hidden */
      show: det.available.filter((k) => !hide.includes(k)),
      entities: { ...det.detected, ...(this._config.entities || {}) },
    };
  }

  _renderPicker() {
    const L = lang(this._hass, this._config);
    const t = tr(this._hass, this._config).editor;
    if (this._picker && this._pickerLang !== L) {
      this._picker.remove();
      this._picker = null;
    }
    this._pickerLang = L;
    if (!this._picker) {
      this._picker = document.createElement("div");
      this._picker.innerHTML = `
        <style>
          .dfp-pick { margin: 0 0 16px; padding: 12px; border: 1px solid var(--divider-color, #ccc); border-radius: 8px; }
          .dfp-pick .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
          .dfp-pick button { font: inherit; padding: 6px 14px; border-radius: 18px; border: 1px solid var(--primary-color, #03a9f4);
            background: transparent; color: var(--primary-color, #03a9f4); cursor: pointer; }
          .dfp-pick button.primary { background: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff); }
          .dfp-pick .hint { font-size: 0.85em; color: var(--secondary-text-color); margin-top: 6px; }
          .dfp-pick .pv { position: relative; display: inline-block; margin-top: 10px; max-width: 160px; }
          .dfp-pick .pv img { display: block; max-width: 160px; max-height: 260px; }
          .dfp-pick .pv .w { position: absolute; outline: 2px solid #ff1744; background: rgba(255, 23, 68, 0.15); }
        </style>
        <div class="dfp-pick">
          <div class="row"><button class="primary" data-a="sim">${t.sim_start}</button></div>
          <div class="hint">${t.sim_hint}</div>
        </div>
        <div class="dfp-pick">
          <div class="label" style="font-weight:500;margin-bottom:8px">${t.stove_picture}</div>
          <label class="lbl" style="display:block;margin:0 0 4px;font-size:0.85em;color:var(--secondary-text-color)">${t.stove_model}</label>
          <select data-a="model" style="font:inherit;padding:6px 8px;border-radius:6px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color);max-width:100%">
            <option value="">${esc(t.stove_model_none)}</option>
            ${STOVE_MODELS.map((m) => `<option value="${m.id}">${esc(m.name)}</option>`).join("")}
          </select>
          <div class="model" style="display:none;margin:8px 0 12px;font-size:0.9em">
            <div class="mi"></div>
            <div style="margin:6px 0"><a class="ml" target="_blank" rel="noopener noreferrer" style="color:var(--primary-color,#03a9f4)">${esc(t.stove_model_link)} ↗</a></div>
            <div class="mhint" style="font-size:0.85em;color:var(--secondary-text-color);line-height:1.45">${t.stove_model_steps.split(/\s(?=\d\.\s)/).map(esc).join("<br>")}</div>
            <div class="mhint" style="font-size:0.85em;color:var(--secondary-text-color);font-style:italic;margin-top:6px">${esc(t.stove_model_copyright)}</div>
          </div>
          <div class="row">
            <button class="primary" data-a="pick">${t.stove_pick}</button>
            <button data-a="remove">${t.stove_remove}</button>
            <input type="file" accept="image/*" hidden>
          </div>
          <div class="hint"></div>
          <div class="pv"><img alt=""><div class="w"></div></div>
        </div>`;
      const input = this._picker.querySelector("input");
      this._picker.querySelector("select[data-a=model]").addEventListener("change", (ev) => {
        const m = STOVE_MODELS.find((x) => x.id === ev.target.value);
        const data = { ...this._form.data, stove_model: m ? m.id : undefined };
        if (m) Object.assign(data, { draught_optimal_from: -m.pa, draught_optimal_to: -DRAUGHT_LIMIT });
        this._changed(data);
      });
      if (!this._onSimDone) {
        this._onSimDone = (ev) => {
          if (!ev.detail || !ev.detail.done || !this._picker) return;
          this._simOn = false;
          this._picker.querySelector("[data-a=sim]").textContent = tr(this._hass, this._config).editor.sim_start;
        };
        window.addEventListener(SIM_EVENT, this._onSimDone);
      }
      this._picker.addEventListener("click", (ev) => {
        const a = ev.target.closest("[data-a]");
        if (!a) return;
        if (a.dataset.a === "pick") input.click();
        if (a.dataset.a === "sim") {
          this._simOn = !this._simOn;
          a.textContent = this._simOn ? t.sim_stop : t.sim_start;
          window.dispatchEvent(new CustomEvent(SIM_EVENT, { detail: { on: this._simOn } }));
        }
        if (a.dataset.a === "remove") this._changed({ ...this._form.data, stove_image: undefined });
      });
      input.addEventListener("change", async () => {
        const file = input.files && input.files[0];
        input.value = "";
        if (!file) return;
        const hint = this._picker.querySelectorAll(".hint")[1];
        hint.textContent = t.stove_loading;
        try {
          const res = await processStoveImage(file);
          this._lastDetect = res.window.found;
          const { found, ...win } = res.window;
          this._changed({ ...this._form.data, stove_image: res.dataUrl, stove_window: { ...win, stove_window_radius: 6 } });
        } catch (e) {
          hint.textContent = t.stove_error;
        }
      });
      this.insertBefore(this._picker, this._form || null);
    }
    const model = STOVE_MODELS.find((x) => x.id === this._config.stove_model);
    this._picker.querySelector("select[data-a=model]").value = model ? model.id : "";
    const mbox = this._picker.querySelector(".model");
    mbox.style.display = model ? "" : "none";
    if (model) {
      mbox.querySelector(".mi").textContent = t.stove_model_info.replace(/\{kw\}/g, model.kw).replace(/\{pa\}/g, model.pa).replace(/\{max\}/g, DRAUGHT_LIMIT);
      mbox.querySelector(".ml").href = model.url;
    }
    const has = !!this._config.stove_image;
    this._picker.querySelector("[data-a=remove]").style.display = has ? "" : "none";
    const pv = this._picker.querySelector(".pv");
    pv.style.display = has ? "" : "none";
    const hint = this._picker.querySelectorAll(".hint")[1];
    if (has) {
      pv.querySelector("img").src = this._config.stove_image;
      const w = { ...DEFAULT_WINDOW, ...(this._config.stove_window || {}) };
      Object.assign(pv.querySelector(".w").style, {
        left: `${w.left}%`,
        top: `${w.top}%`,
        width: `${w.width}%`,
        height: `${w.height}%`,
        borderRadius: `${this._config.stove_window_radius ?? 4}px`,
      });
      hint.textContent = this._lastDetect === false ? t.stove_not_found : t.stove_hint;
    } else {
      hint.textContent = t.stove_none;
    }
  }

  _changed(value) {
    const det = this._det || this._detect();
    const cfg = { ...value };
    /* show list -> hide list (only elements this device provides) */
    const show = Array.isArray(cfg.show) ? cfg.show : det.available;
    const oldHide = hideList(this._config);
    cfg.hide = [...new Set([...det.available.filter((k) => !show.includes(k)), ...oldHide.filter((k) => !det.available.includes(k))])];
    delete cfg.show;
    if (cfg.stove_window && typeof cfg.stove_window === "object") {
      const { stove_window_radius: rad, ...win } = cfg.stove_window;
      if (rad !== undefined) cfg.stove_window_radius = rad;
      cfg.stove_window = win;
    }
    if (!cfg.stove_image) {
      delete cfg.stove_window;
      delete cfg.stove_window_radius;
      delete cfg.stove_window_debug;
    }
    /* only keep entities that differ from the detected ones */
    const ents = {};
    for (const [k, v] of Object.entries(cfg.entities || {})) if (v && v !== det.detected[k]) ents[k] = v;
    if (Object.keys(ents).length) cfg.entities = ents;
    else delete cfg.entities;
    if (cfg.device && cfg.device === det.device && !this._config.device) delete cfg.device;
    for (const [k, v] of Object.entries(DEFAULTS)) if (cfg[k] === v && this._config[k] === undefined) delete cfg[k];
    for (const k of Object.keys(cfg)) {
      if (cfg[k] === "" || cfg[k] === undefined || cfg[k] === false && k === "stove_window_debug" || (Array.isArray(cfg[k]) && cfg[k].length === 0 && k !== "hide"))
        delete cfg[k];
    }
    if (cfg.translations && (typeof cfg.translations !== "object" || !Object.keys(cfg.translations).length)) delete cfg.translations;
    this._config = cfg;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: cfg }, bubbles: true, composed: true }));
    this._render();
  }
}

if (!customElements.get("drooff-fireplus-card")) customElements.define("drooff-fireplus-card", DrooffFireplusCard);
if (!customElements.get("drooff-fireplus-card-editor"))
  customElements.define("drooff-fireplus-card-editor", DrooffFireplusCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "drooff-fireplus-card")) {
  window.customCards.push({
    type: "drooff-fireplus-card",
    name: "Drooff fire+ Card",
    description: "Kaminofen mit Flammenanimation und Werten der Drooff fire+ Abbrandsteuerung",
    preview: true,
    documentationURL: "https://github.com/tehlers/ha-drooff-fireplus",
  });
}

console.info(`%c DROOFF-FIREPLUS-CARD %c ${CARD_VERSION} `, "color:#fff;background:#f4511e;font-weight:700", "color:#f4511e");
