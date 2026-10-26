# Inkbird INT Cook Control

Four probes, food and ambient temperatures, a graph of the cook and an alert you
can actually hear. Cook Control is an optional dashboard maintained here alongside
the Inkbird INT integration. You can keep using your own dashboards instead.

[Guida in italiano](README.it.md) | [Test results and limits](VALIDATION.md)

**Optional dashboard, available with integration release v0.2.10.** This version is for
**one INT-14-BW station**. Its two-channel probe diagram is deliberately different
from the five-channel INT-14S/INT-12E layout. Do not force another model into it.

## Install

Start with the Inkbird INT integration working and all eight food/ambient entities
enabled. Install **button-card**, **card-mod** and **mini-graph-card** from HACS.
This package was tested on HA **2026.10.4**.

**[Download Cook Control](https://github.com/zampix1/ha-inkbird-int14/releases/download/v0.2.10/inkbird-int-cook-control.zip)**

Extract the ZIP first. The HA configuration directory is the folder containing
`configuration.yaml` (normally `/config`). Merge the two folders into it; do not
put the entire ZIP or an extra `inkbird-int-cook-control` parent folder there:

```text
config/
  configuration.yaml
  packages/inkbird_bbq.yaml
  www/inkbird-int/cook-base-v1.4.3.js
  www/inkbird-int/inkbird-int-cook-model.mjs
  www/inkbird-int/inkbird-int-cook-control.js
```

The ZIP's `cook-control` folder contains the guides, licenses and dashboard YAML;
it does not need to be copied into HA.

1. Make a HA backup. Copy `packages` and `www` from the Cook Control bundle into
   your HA configuration directory. The source equivalents are beside this guide.
   **Replace an existing `inkbird_bbq.yaml`; never load two BBQ packages.**
   Existing helper IDs are preserved so upgrades retain targets and names.
2. If packages are not configured, add this beneath the existing `homeassistant:`
   section in `configuration.yaml`. Do not duplicate that section:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   Check the configuration, then restart HA. Different include layout? See the
   [HA package guide](https://www.home-assistant.io/docs/configuration/packages/).
3. In **Settings > Dashboards > Resources**, add the JavaScript module
   `/local/inkbird-int/inkbird-int-cook-control.js?v=1.0.4`.
   Enable Advanced mode in your HA profile if Resources is hidden. When upgrading,
   edit the existing resource URL instead of adding a duplicate. Reload the browser.
4. Add **Inkbird Cook Control** from the Community dashboards section. If that
   choice is not shown, create an empty dashboard and paste [dashboard.yaml](dashboard.yaml)
   into its raw configuration editor:

   ```yaml
   strategy:
     type: custom:inkbird-int-cook-control
   views: []
   ```

5. On first opening, confirm **Use this thermometer**. With one INT-14-BW, it is
   detected automatically. This sets the shared prefix once, not in several files.
   No thermometer settings are written.

If discovery is ambiguous, add `prefix: sensor.your_inkbird` under `strategy:`.
Find it by removing `_probe_1_internal_temperature` from your probe 1 food entity.
A different configured model is rejected. This package has one shared set of
helpers; multiple independent stations are not supported yet.

HACS installs the integration, **not this optional package**. There is no second
custom integration to install. Maintainers can produce the copy-ready ZIP with
`python examples/cook_control/build_bundle.py --output /path/to/inkbird-int-cook-control.zip`.

## Start A Cook

Give the probe a name, tap its card to edit the HA target, then turn on **Probe
alerts** for the probes you use. Unused probes can show room temperature without
announcing anything. For a new cook, switch that probe's alerts off and back on.

- **HA target** drives dashboard notifications. Recipe buttons change helpers,
  not the thermometer's firmware alarm.
- **Station alarm** displays the device's reported threshold. Its physical sound
  switch and alarm remain independent of HA.

A target alert fires after 30 continuous seconds at or above the target, once
per armed cook rather than after every reconnect. Changing the name, target or
thermometer cancels pending reminders. **Dismiss** cancels both snooze and the
optional post-target reminder. A new **Snooze** replaces the previous one.

The reminder is timed from the HA target, **not** from removal from heat.
Targets and recipe presets are not food-safety assessments or guarantees of
doneness. Check the cook yourself.

## Echo And TV

In Settings, refresh devices, select your Echo, choose **Alexa (native)** and
enable announcements. It needs a working **Alexa Media Player** installation,
not OpenAI or a TTS API key.

For TV text, enter its `media_player` entity and notify service name without
`notify.`. Enable TV alerts and press **Test notification**. The tested LG webOS
popup is brief and **silent**. Cook Control does not turn on the TV, change inputs,
alter the volume or interrupt the programme with audio.

Persistent HA notifications are created first. Optional phone, TV and speech
outputs follow. Invalid speech settings produce a visible error. A successful
service call is not proof of physical delivery: test your own outputs.

Choose **English** or **Italiano** in Settings. Core labels and target announcements
follow it; some inherited recipe and advanced-setting labels remain English.

## Connection And Timer Limits

The header distinguishes a normal BLE gap from stale data. After 120 seconds
without a local packet, status stops qualifying for a new target alarm. HA's
minute-based template clock can delay that boundary by up to a minute. Cloud
history is not treated as a live cooking feed.

Battery percentages come from the station. Suspect reports are flagged and do
not trigger a low-battery alert. Optional stall detection requires 45 continuous
minutes of fresh, below-target data changing by less than 1 C/hour.

Timers do not survive HA restarts or automation reloads. HA cannot notify you
while it is down. These are advisory alerts, not safety systems.

## Sources And Rollback

**zampix1/ha-inkbird-int14** supplies device communication, protocol handling and
probe entities. This project maintains the adapted presentation and alarms.
The visual base comes from Remco's MIT-licensed `remb0/inkbird-dashboard` v1.4.3.
The generic Alexa/TV patch is also offered in
[upstream PR #4](https://github.com/remb0/inkbird-dashboard/pull/4).
Remco credits Boris Pustilnik for Cook Control's **dashboard design**, not this
integration's protocol implementation. See [third-party notices](THIRD_PARTY_NOTICES.md).
No code is fetched from Remco's repository at runtime.

To roll back, restore the previous package and dashboard, check the configuration
and restart HA. Remove the resource only when no dashboard uses it. Do not delete
the Inkbird integration or pair the station again.
