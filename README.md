# SiePomaga — Home Assistant integration (HACS)

Custom integration for Home Assistant to track fundraising campaigns from [SiePomaga.pl](https://www.siepomaga.pl), installable via HACS.

> Status: **Production ready** — Full-featured integration with support for active and completed fundraisers.

## Installation

### 3. Dodać repo w HACS (custom repository)

1. W Home Assistant wejdź w **HACS** (pasek boczny).
2. Kliknij **Integracje** (Integrations).
3. Kliknij **⋮** (trzy kropki) w prawym górnym rogu.
4. Wybierz **Custom repositories** (Niestandardowe repozytoria).
5. W polu **Repository** wklej:  
   `https://github.com/sasiela/siepomaga`
6. W **Category** wybierz **Integration**.
7. Kliknij **Add** (Dodaj).

### 4. Zainstalować integrację przez HACS

1. W HACS → **Integracje** wyszukaj **SiePomaga** (lub odśwież listę).
2. Kliknij **SiePomaga** → **Download** (Pobierz).
3. Po zakończeniu pobierania **zrestartuj Home Assistant** (Ustawienia → System → Restart).
4. Po restarcie: **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
5. Wyszukaj **SiePomaga**, wybierz i dodaj.
6. Wklej slug zbiórki (np. `pawelek-pokropek`) lub pełny URL i dokończ konfigurację.

---

### Szybka ścieżka (skrót)

1. **HACS → Integrations → ⋮ → Custom repositories** → dodaj `https://github.com/sasiela/siepomaga`, kategoria **Integration**.
2. W HACS wyszukaj **SiePomaga** → **Download** → restart HA.
3. **Ustawienia → Urządzenia i usługi → Dodaj integrację → SiePomaga** → wklej slug/URL zbiórki.

### Ikona w HACS / na liście integracji

Ikona w HACS i w HA pochodzi z repozytorium [Home Assistant Brands](https://github.com/home-assistant/brands). W tym repo są już pliki **icon.png** (256×256) i **icon@2x.png** (512×512).

Aby ikona pojawiła się na liście integracji w HACS i w HA:

1. Zrób fork [home-assistant/brands](https://github.com/home-assistant/brands).
2. W forku utwórz katalog `custom_integrations/siepomaga/`.
3. Skopiuj z tego repo pliki `icon.png` i `icon@2x.png` do `custom_integrations/siepomaga/`.
4. Otwórz Pull Request do repozytorium `home-assistant/brands`.

Po zaakceptowaniu PR ikona będzie dostępna pod `https://brands.home-assistant.io/siepomaga/icon.png` i pojawi się w HACS/HA (może być potrzebny czas na aktualizację cache).

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

