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

### Ikona w HACS / na liście integracji (Home Assistant Brands)

Ikona w HACS i w HA jest serwowana z repozytorium [home-assistant/brands](https://github.com/home-assistant/brands). W **tym** repo (siepomaga) masz już pliki **icon.png** (256×256) i **icon@2x.png** (512×512). Żeby ikona pojawiła się w interfejsie, musisz dodać je do repozytorium Brands — krok po kroku:

---

#### Krok 1: Zaloguj się na GitHub

- Wejdź na [github.com](https://github.com) i zaloguj się na swoje konto.

#### Krok 2: Zrób fork repozytorium Brands

- Otwórz: **[https://github.com/home-assistant/brands](https://github.com/home-assistant/brands)**  
- Kliknij przycisk **„Fork”** (prawy górny róg).  
- GitHub utworzy kopię repozytorium pod Twoim kontem (np. `https://github.com/TWOJ_LOGIN/brands`).

#### Krok 3: Otwórz fork na swoim koncie

- Wejdź w **swoje** repozytorium (np. **Your username / brands**).  
- Upewnij się, że jesteś na gałęzi **master** (dropdown „Branch” u góry).

#### Krok 4: Utwórz folder dla integracji

- Kliknij folder **`custom_integrations`**.  
- Kliknij **„Add file”** → **„Create new file”**.  
- W ścieżce pliku wpisz: **`custom_integrations/siepomaga/icon.png`** (nazwa folderu `siepomaga` i pliku `icon.png`).  
- Na razie **nie wklejaj** jeszcze obrazka — najpierw usuń ścieżkę i utwórz sam folder:
  - Zamiast tego w górnym pasku ścieżki kliknij **`custom_integrations`**, wróć do widoku folderów.
  - W polu „Name your file...” wpisz: **`siepomaga/icon.png`** — GitHub utworzy folder `siepomaga` przy dodaniu pliku.

*Prostsza metoda:* na swoim komputerze sklonuj swój fork, dodaj pliki lokalnie i wypchnij zmiany (patrz Krok 5 alternatywa).

#### Krok 5: Dodaj pliki ikon

**Opcja A — przez przeglądarkę (dla jednego pliku):**

- W forku: **custom_integrations** → **„Add file”** → **„Upload files”**.  
- Utwórz folder: w nazwie pliku podaj **`siepomaga/icon.png`** (możesz przeciągnąć plik **icon.png** z tego repo).  
- Potem dodaj drugi plik **icon@2x.png** w ten sam folder **siepomaga** („Upload files” → **siepomaga/icon@2x.png**).  
- Na dole strony wpisz tytuł commita (np. **Add SiePomaga integration icon**) i kliknij **„Commit changes”**.

**Opcja B — na komputerze (git):**

```bash
git clone https://github.com/TWOJ_LOGIN/brands.git
cd brands
mkdir -p custom_integrations/siepomaga
cp /ścieżka/do/siepomaga/icon.png custom_integrations/siepomaga/
cp /ścieżka/do/siepomaga/icon@2x.png custom_integrations/siepomaga/
git add custom_integrations/siepomaga/
git commit -m "Add SiePomaga integration icon"
git push origin master
```

(Zamień `TWOJ_LOGIN` na swój login GitHub i `/ścieżka/do/siepomaga/` na folder z tym repozytorium, gdzie leżą `icon.png` i `icon@2x.png`.)

#### Krok 6: Otwórz Pull Request

- Wejdź na **swoj** fork: `https://github.com/TWOJ_LOGIN/brands`.  
- GitHub często pokazuje żółty pasek: **„Compare & pull request”** — kliknij go.  
- Jeśli nie: idź na [github.com/home-assistant/brands](https://github.com/home-assistant/brands) → zakładka **„Pull requests”** → **„New pull request”** → **„compare across forks”** → base: **home-assistant/brands**, compare: **TWOJ_LOGIN/brands**, branch **master**.  
- Tytuł np.: **Add SiePomaga integration icon**.  
- W opisie możesz napisać: „Add icon for custom integration SiePomaga (siepomaga.pl).”  
- Kliknij **„Create pull request”**.

#### Krok 7: Po zaakceptowaniu PR

- Maintainerzy Home Assistant zmergują PR.  
- Ikona będzie dostępna pod: **https://brands.home-assistant.io/siepomaga/icon.png**  
- W HACS i w HA ikona może pojawić się z opóźnieniem (cache do ok. 24 h).

---

**Wymagania dla ikon (zgodnie z [brands README](https://github.com/home-assistant/brands)):** PNG, 256×256 (`icon.png`), 512×512 (`icon@2x.png`), proporcje 1:1. Pliki w tym repo już to spełniają.

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

