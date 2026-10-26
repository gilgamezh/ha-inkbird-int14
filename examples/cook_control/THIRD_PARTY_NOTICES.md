# Dashboard Sources

The integration `inkbird_int14` is maintained in `zampix1/ha-inkbird-int14`.
It is separate from the optional dashboard sources below.

## Remco's Dashboard

Source: https://github.com/remb0/inkbird-dashboard

Base: v1.4.3, commit `190a196f941bbc5495d3bc5381eedd8f53c5122e`.

Generic announcement patch: `8816b15` on
https://github.com/zampix1/inkbird-dashboard/tree/fix/native-alexa-tv-notifications

The generated base bundle and YAML package include adapted portions. The bundle's
custom-element registration is namespaced to avoid colliding with an existing
Remco dashboard. Installation-specific example prefixes are replaced by a
placeholder. Further presentation and per-probe alert changes are maintained
by this project. Remco's MIT notice is preserved in [LICENSE.remb0](LICENSE.remb0).

## Cook Control Design

Remco credits https://github.com/boris327/ha-inkbird-int14bw for the Cook Control
design foundation; its MIT notice is retained in [LICENSE.boris](LICENSE.boris).
This does not mean that `zampix1/ha-inkbird-int14` uses Boris's
device integration. The bundled base also retains the original community credits
for Nexus1212's multi-sensor dashboard, button-card, card-mod and mini-graph-card.

The external frontend cards remain separately installed dependencies and retain
their own licenses. No Inkbird app code, credentials or captured device data are
included in this example.
