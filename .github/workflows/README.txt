# TruckNavigator workflow replacements

These are the ONLY workflow files changed in this repair package.

Changed:
- build-dynamic-lanes-europe.yml
- build-ip-card-network.yml
- build-offline-service-areas-europe.yml
- build-road-safety-pbf-v10.yml

Common repair:
- do not download Geofabrik `*-latest.osm.pbf` directly;
- fetch the official country index;
- resolve the newest dated `slug-YYYYMM.osm.pbf` entry;
- download the dated PBF directly;
- verify it is non-empty before invoking the existing builder.

No builder logic, country scope, database schema, manifest structure, or publish logic was intentionally changed.

Do NOT replace the other four workflows just for this repair:
- build-roundabouts-europe.yml (already has the dated-PBF resolver)
- build-fuel-card-networks.yml
- keep-scheduled-workflows-alive.yml
- update-road-safety.yml

Repository source was read from the current default branch before preparing these files.
