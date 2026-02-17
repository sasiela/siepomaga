# SiePomaga — Home Assistant integration (HACS)

Custom integration for Home Assistant to track fundraising campaigns from [SiePomaga.pl](https://www.siepomaga.pl), installable via HACS.

> Status: **Production ready** — Full-featured integration with support for active and completed fundraisers.

## Installation

### HACS (Custom repository)

1. In Home Assistant: **HACS → Integrations → ⋮ → Custom repositories**
2. Add this GitHub repository URL and select category **Integration**
3. Search for **SiePomaga** in HACS and install
4. Restart Home Assistant
5. Go to **Settings → Devices & services → Add integration → SiePomaga**

### Manual

1. Copy `custom_components/siepomaga/` into your Home Assistant `config/custom_components/siepomaga/`
2. Restart Home Assistant

## Configuration

Configured via UI (config flow). Paste a fundraiser slug (e.g. `pawelek-pokropek`) or full URL (e.g. `https://www.siepomaga.pl/pawelek-pokropek`).

The integration creates 3 sensors:

- `Zebrano` (PLN)
- `Brakuje` (PLN)
- `Postęp` (%)

Additional sensors:

- `Cel` (PLN) — calculated as `zebrano + brakuje` (when both are present)
- `Wspierających` (osób)
- `Stałych pomagaczy` (osób)
- `Rozpoczęcie` (date)
- `Zakończenie` (date)

### Options

You can change the refresh interval in the integration options (`scan_interval`, seconds).

## Development notes

- Domain: `siepomaga`
- Code location: `custom_components/siepomaga/`

