# Inkbird INT for Home Assistant

Your food thermometer, alongside the rest of your home.

Bring probe temperatures, battery readings and supported local controls into Home Assistant. Start with Bluetooth, or use local Wi-Fi on models with a validated Tuya LAN connection.

[![Available in HACS](https://img.shields.io/badge/HACS-default_catalog-41BDF5?logo=homeassistant&logoColor=white)](https://github.com/hacs/default/pull/9786)
[![Latest release](https://img.shields.io/github/v/release/zampix1/ha-inkbird-int14?label=release&color=18794e)](https://github.com/zampix1/ha-inkbird-int14/releases/latest)
[![License: MIT](https://img.shields.io/github/license/zampix1/ha-inkbird-int14)](https://github.com/zampix1/ha-inkbird-int14/blob/main/LICENSE)

<p align="center">
  <img src="https://raw.githubusercontent.com/zampix1/ha-inkbird-int14/main/docs/images/int14-product.jpg" alt="Inkbird INT-14-BW base station with four wireless probes" width="480">
</p>

*The INT-14-BW is the tested baseline: four physical probes, each with food and ambient temperature readings. Related models have their own support limits below.*

[![Open Inkbird INT in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=zampix1&repository=ha-inkbird-int14&category=integration)

[User guides](https://github.com/zampix1/ha-inkbird-int14/wiki) | [Model details](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/model_profiles.md) | [Questions and community](https://github.com/zampix1/ha-inkbird-int14/discussions) | [Report a bug](https://github.com/zampix1/ha-inkbird-int14/issues/new?template=bug_report.yml)

## Choose Your Model

Similar-looking stations do not always use the same protocol. Select the model printed on your device, rather than the closest-looking one.

Alongside the INT-14-BW pictured above, these models have been tested by community members:

| **INT-14S-BW** | **INT-12E-BW** | **INT-11I-B** |
| :---: | :---: | :---: |
| <img src="https://raw.githubusercontent.com/zampix1/ha-inkbird-int14/main/docs/images/int14s-product.jpg" alt="Blue INT-14S-BW base station with four wireless probes" width="200"> | <img src="https://raw.githubusercontent.com/zampix1/ha-inkbird-int14/main/docs/images/int12e-product.jpg" alt="INT-12E-BW base station with black and white wireless probes" width="200"> | <img src="https://raw.githubusercontent.com/zampix1/ha-inkbird-int14/main/docs/images/int11i-product.jpg" alt="White INT-11I-B charging base with one wireless probe" width="200"> |
| 4 physical probes, **20 temperature channels** | 2 physical probes, **10 temperature channels** | 1 probe temperature mapped |
| Community-validated readings; read-only in normal use | Community-validated BLE readings; read-only | Experimental community-tested BLE readings; read-only |

*Photos identify the hardware, not the features supported by this integration. The table below shows which connections and controls are available for each model.*

| Model | Probe temperatures | Connection | Current support |
| --- | --- | --- | --- |
| **INT-14-BW** | 4 probes, food + ambient each: **8 channels** | Local BLE and Tuya LAN | Tested baseline, including validated local controls. |
| **INT-14S-BW** | 4 probes, 4 food + ambient each: **20 channels** | BLE; experimental read-only Tuya LAN | Community-validated readings. Normal operation is read-only. |
| **INT-12E-BW** | 2 probes, 4 food + ambient each: **10 channels** | BLE, including ESPHome Bluetooth Proxy | Community-validated temperature and battery readings. Read-only. |
| **INT-11I-B** | 1 probe temperature | Connected BLE GATT reads | Experimental community-tested temperature and base/probe battery readings. Read-only. |

Station temperature is additional where supported. Other model profiles range from experimental to **cataloged only**; being listed does not mean live readings or controls are available. Check the [full profile table](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/model_profiles.md) before setting up another model.

## Install From HACS

Inkbird INT is in the **default HACS catalog**. You do not need to add a custom repository.

1. Open **HACS** and search for **Inkbird INT**.
2. Open the result and download the integration.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration**, search for **Inkbird INT**, and select your exact model profile.

Already using an earlier version? Update through HACS and restart Home Assistant once. Keep your existing integration entry and thermometer pairing.

The current stable release is **v0.2.9**. It adds product photos for the community-tested models to the GitHub/HACS presentation. The installation guides from **v0.2.8** and the Options and reconfiguration fixes from **v0.2.7** are included; thermometer protocol support is unchanged.

Without HACS, follow the [manual installation steps](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/configuration.md#manual-installation).

## See It In Home Assistant

The integration creates Home Assistant entities. You can use them in your own dashboard, history graphs, notifications and automations.

### INT-14-BW Readings

![INT-14-BW card preview with food and ambient temperatures, station and probe batteries, and the active local transport](https://raw.githubusercontent.com/zampix1/ha-inkbird-int14/main/docs/images/int14-ha-card.png)

*A sanitized presentation of captured INT-14-BW readings. This is an example, not a dashboard installed automatically by the integration.*

### A Dashboard From The Community

![INT-12E-BW Home Assistant dashboard showing both multisensor probes, batteries and temperature history](https://raw.githubusercontent.com/zampix1/ha-inkbird-int14/main/docs/images/community/int12e-dashboard.png)

Shared by [@Nexus1212](https://github.com/Nexus1212). The probe artwork, channel labels and graphs make the five sensors on each INT-12E-BW probe easier to follow. The [dashboard guide and example YAML](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/int12e_dashboard.md) are available if you want to build a similar view. The example uses standard Home Assistant cards.

## Pick A Connection

### Bluetooth

Use a local Home Assistant Bluetooth adapter or an **ESPHome Bluetooth Proxy** near the station. The proxy is optional: you do not need an ESP32 if your existing adapter has sufficient range.

Close the Inkbird app while testing if it is competing for the same BLE connection. Snapshot and continuous-update behaviour depends on the selected model; the [Bluetooth guide](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/bluetooth_proxy.md) explains the available paths.

### Local Wi-Fi

The station must already be on your network, and the selected model must support Tuya LAN. Setup asks for:

- the station **host or IP**;
- its **device ID** and **local key**;
- the protocol version, usually **3.5** on the tested INT-14-BW;
- the polling interval.

The integration does not retrieve the local key for you. It is a per-device credential, not your Wi-Fi or Inkbird password. The [LAN setup guide](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/lan_setup.md) covers where those values come from and why some app accounts do not appear in the usual Tuya tools.

With a complete LAN configuration, **Auto** prefers local Wi-Fi and avoids keeping BLE connected continuously. Transport modes and their model-specific limits are explained in the [configuration guide](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/configuration.md).

### Optional Cloud History

Experimental cloud history is **off by default** and reads DP109 temperature history only, for supported profiles. It does not provide complete live cloud readings or cloud writes. Local BLE and LAN operation do not require this feature. See the [cloud history notes](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/cloud_history_experimental.md) before enabling it.

## Readings And Controls

Depending on your model, the integration exposes probe temperatures, station temperature, reported batteries, transport status and supported settings. Useful entities are enabled first; noisy or unvalidated diagnostic fields are hidden or disabled by default.

On **INT-14-BW**, validated local operations include temperature unit, display light, targets, pre-alarm, timers and calibration. Availability depends on the selected transport and the data the station supplies.

**INT-14S-BW, INT-12E-BW and INT-11I-B are read-only in normal use.** INT-14S has separate, disabled-by-default diagnostic write tests; these are not general-purpose alarm or settings controls. See the [LAN diagnostic notes](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/lan_diagnostics.md) before opting in.

## A Few Things To Know

- **A profile name is not a support promise.** Cataloged models have no fake live temperature entities, and their live transports and writes remain blocked.
- **Battery percentages come from the station.** Some stations report 100% for long periods. Battery quality diagnostics can flag repeated plateaus; the integration cannot turn that value into an independent measurement.
- **The BLE fallback interval does not throttle notifications.** For INT-12E-BW, notifications may update readings more often than the default 10-second fallback read. The fallback interval is configurable from 5 to 300 seconds.
- **INT-12E-BW may close BLE sessions after about 30 seconds.** The integration reconnects automatically. A disconnected instant does not necessarily mean the integration has stopped working.
- **A model-specific LAN map is required.** Wi-Fi working in the official app does not guarantee that this integration can use local Wi-Fi on the same model.
- **Custom dashboards are optional examples.** Installing this integration creates entities, not the pictured dashboard layout.

More detail: [model profiles](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/model_profiles.md) and [configuration](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/configuration.md).

## Guides And Help

| I want to... | Start here |
| --- | --- |
| Check my exact model | [Model profiles](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/model_profiles.md) |
| Set up local Wi-Fi or find the required credentials | [Tuya LAN setup](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/lan_setup.md) |
| Use an ESPHome proxy instead of a nearby USB adapter | [Bluetooth and proxy guide](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/bluetooth_proxy.md) |
| Understand Options, transport and entity availability | [Configuration guide](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/configuration.md) |
| Build the multisensor probe dashboard | [Community dashboard](https://github.com/zampix1/ha-inkbird-int14/blob/main/docs/int12e_dashboard.md) |
| Help validate a model | [Model validation report](https://github.com/zampix1/ha-inkbird-int14/discussions/new?category=q-a) |
| Ask a setup question | [Discussions](https://github.com/zampix1/ha-inkbird-int14/discussions) |
| Report a reproducible problem | [Bug report](https://github.com/zampix1/ha-inkbird-int14/issues/new?template=bug_report.yml) |

Before posting diagnostics, logs or screenshots, remove addresses, device IDs, local keys, tokens, Wi-Fi names and identifying entity IDs. Never attach a Tuya `devices.json` file. See [Security](https://github.com/zampix1/ha-inkbird-int14/blob/main/SECURITY.md) for private reports.

## Contributing And Support

Real-device reports are how new profiles become useful. Please include your exact model, transport, number of physical probes, temperature channels shown in the app and which readings or controls worked. For multisensor probes, a controlled tip/body/ambient test is particularly helpful. The [contribution guide](https://github.com/zampix1/ha-inkbird-int14/blob/main/CONTRIBUTING.md) has the details.

If the integration is useful to you, a star or a [GitHub sponsorship](https://github.com/sponsors/zampix1) is appreciated. Testing, bug reports and clear setup notes help too.

## About This Project

This is an independent community integration. It is **not affiliated with, endorsed by or supported by Inkbird**. Product photos identify the hardware; photo credits and source pages are listed in the [third-party notices](https://github.com/zampix1/ha-inkbird-int14/blob/main/THIRD_PARTY_NOTICES.md#product-photographs). Inkbird names, logos and trademarks belong to their respective owners.

The repository keeps the name `ha-inkbird-int14` for continuity with the original INT-14-BW implementation, existing installs and links. Its public integration name is **Inkbird INT**; the Home Assistant domain remains `inkbird_int14`.

BLE authentication includes MIT-licensed code adapted from [paul43210/inkbird-bw-ble](https://github.com/paul43210/inkbird-bw-ble). See [Third-party notices](https://github.com/zampix1/ha-inkbird-int14/blob/main/THIRD_PARTY_NOTICES.md). Before installing any custom integration, check whether Home Assistant core already supports your exact model.
