# Changelog

All notable changes to this SDK are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and
this project follows [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-06-12


### Features

- Per-application endpoint cap (max_endpoints) and Developer Portal event-catalog toggle (show_event_types) on the applications resource, with an UNSET sentinel for tri-state updates

## [0.1.4] - 2026-06-01

### Documentation

- Removed endpoint metadata field from the README endpoint-creation example. The SDK still accepts `metadata` in `endpoints.create()` payloads for backward compatibility — only the example was scrubbed while metadata is not yet a queryable / filterable field.

## [0.1.3] - 2026-05-31

### Features

- Add Deliveries resource to NahookManagement

## [0.1.2] - 2026-05-25

### Features

- Expose optional environmentId on endpoints.create
- Add environments resource to the management client

## [0.1.1] - 2026-04-28

### Features

- Add environments resource to the management client
- Embed workspace region in API keys for SDK auto-routing

### Bug Fixes

- Add PyPI classifiers
- Declare hypothesis dev dep + correct Repository URL
- Finish maintainer-identity unification

## [0.1.0] - 2026-04-10

### Features

- Initial release of the Nahook Python SDK
