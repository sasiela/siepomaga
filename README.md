# SiePomaga — Home Assistant integration (HACS)

Custom integration for Home Assistant to track fundraising campaigns from [SiePomaga.pl](https://www.siepomaga.pl), installable via HACS.

> Status: **Production ready** — Full-featured integration with support for active and completed fundraisers.

## Installation

### 1. Dodać repo w HACS (custom repository)

1. W Home Assistant wejdź w **HACS** (pasek boczny).
2. Kliknij **Integracje** (Integrations).
3. Kliknij **⋮** (trzy kropki) w prawym górnym rogu.
4. Wybierz **Custom repositories** (Niestandardowe repozytoria).
5. W polu **Repository** wklej:  
   `https://github.com/sasiela/siepomaga`
6. W **Category** wybierz **Integration**.
7. Kliknij **Add** (Dodaj).

### 2. Zainstalować integrację przez HACS

1. W HACS → **Integracje** wyszukaj **SiePomaga** (lub odśwież listę).
2. Kliknij **SiePomaga** → **Download** (Pobierz).
3. Po zakończeniu pobierania **zrestartuj Home Assistant** (Ustawienia → System → Restart).
4. Po restarcie: **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
5. Wyszukaj **SiePomaga**, wybierz i dodaj.
6. Wklej slug zbiórki (np. `pawelek-pokropek`) lub pełny URL i dokończ konfigurację.

---

### 3. Szybka ścieżka (skrót)

1. **HACS → Integrations → ⋮ → Custom repositories** → dodaj `https://github.com/sasiela/siepomaga`, kategoria **Integration**.
2. W HACS wyszukaj **SiePomaga** → **Download** → restart HA.
3. **Ustawienia → Urządzenia i usługi → Dodaj integrację → SiePomaga** → wklej slug/URL zbiórki.

### 4. Instalacja ręczna (Manual)

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
- `Wpływy dzienne` (PLN) — kwota wpływu **dziś**; atrybut `wpływy_na_dzień` zawiera historię (lista `{date, amount}` z ostatnich ~31 dni) do wykresu słupkowego
- `Wspierających` (osób)
- `Stałych pomagaczy` (osób)
- `Rozpoczęcie` (date)
- `Zakończenie` (date)

### Gdzie są ustawienia pluginu (opcje)

Możesz zmienić **interwał odświeżania** (np. co 300 sekund) w opcjach integracji.

**Zaktualizuj integrację** (HACS → SiePomaga → Aktualizuj) i **zrestartuj Home Assistant**. W nowszej wersji opcje są rejestrowane inaczej, dzięki czemu przycisk **„Konfiguruj”** powinien się pojawić.

Gdzie szukać:

1. **Ustawienia** → **Urządzenia i usługi**.
2. Znajdź **SiePomaga** (wyszukaj „SiePomaga” w górnym polu).
3. Kliknij **w nazwę wpisu** (np. **„SiePomaga: pawelek-pokropek”**) — otworzy się strona urządzenia.
4. Na stronie urządzenia szukaj przycisku **„Konfiguruj”** (lub **„Configure”**) albo **ikony zębatki** / **trzy kropki (⋮)** → **Konfiguruj**.
5. Otworzy się okno z polem **„Częstotliwość odświeżania (sekundy)”** (domyślnie 300) — zmień i zapisz.

**Jeśli nadal nie ma „Konfiguruj”:** w **Urządzenia i usługi** kliknij **trzy kropki (⋮)** przy **karcie integracji SiePomaga** (nie przy pojedynczym wpisie) i zobacz, czy w menu jest **„Konfiguruj”** lub **„Opcje”**.

**Obejście:** usuń integrację (⋮ → Usuń) i dodaj ją ponownie (Dodaj integrację → SiePomaga → wklej slug). Domyślny interwał to 300 s; zmiana będzie możliwa po pojawieniu się opcji w Twojej wersji HA.

### Integracja nic nie pobiera (sensory „Unknown”)

- **W opcjach** włącz **„Zapisuj błędy do logów”** i zapisz. Po następnym odświeżeniu (lub po kilku minutach) sprawdź **Ustawienia → System → Logi** (filtr: `siepomaga`).
- Jeśli w logu jest **„Timeout loading …”** — problem z siecią/DNS lub strona siepomaga.pl nie odpowiada w czasie.
- Jeśli jest **„Odpowiedź … wygląda na niepełną (brak 'zł' …)”** — serwer zwrócił inną stronę (np. cookie consent). W logu zobaczysz początek odpowiedzi; w takiej sytuacji integracja nie może wyciągnąć danych z takiej strony.
- Upewnij się, że HA ma dostęp do internetu i że adres `https://www.siepomaga.pl/` nie jest blokowany (firewall, pi-hole itd.).

## Development notes

- Domain: `siepomaga`
- Code location: `custom_components/siepomaga/`

