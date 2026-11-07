# Integration Quality Scale

Status of this integration against the rules of the
[Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/).
Custom integrations are not graded by Home Assistant; this list documents the state of the code.

| Tier | Rule | Status |
| --- | --- | --- |
| Bronze | config-flow, unique-config-entry, test-before-configure, test-before-setup | done |
| Bronze | entity-unique-id, has-entity-name, runtime-data, common-modules | done |
| Bronze | appropriate-polling (default 5 s, configurable 1–60 s) | done |
| Bronze | action-setup, docs-actions | exempt (no custom actions) |
| Bronze | brands | todo (no logo in home-assistant/brands) |
| Bronze | config-flow-test-coverage | done (tests/) |
| Silver | entity-unavailable, log-when-unavailable, config-entry-unloading | done |
| Silver | action-exceptions (translated `HomeAssistantError` when a write fails) | done |
| Silver | parallel-updates (`0` for read-only platforms, `1` for number/switch) | done |
| Silver | integration-owner | done |
| Silver | reauthentication-flow | exempt (the fire+ has no authentication) |
| Gold | devices (manufacturer, model, firmware, serial number) | done |
| Gold | diagnostics | done |
| Gold | discovery (DHCP, hostname `fire`) | done |
| Gold | entity-category, entity-device-class, entity-disabled-by-default | done |
| Gold | entity-translations, exception-translations, icon-translations | done |
| Gold | reconfiguration-flow | done |
| Gold | dynamic-devices, stale-devices | exempt (one device per config entry) |
| Gold | repair-issues | exempt (no user-fixable issues) |
| Platinum | async-dependency, inject-websession | done |
| Platinum | strict-typing | todo |

The `operation_status` sensor reports lower-case states (`regular`, `heating`, …) so Home
Assistant translates them. Up to version 1.5 they were upper-case; automations comparing them
have to be updated (the blueprint of the integration already uses the new states).
