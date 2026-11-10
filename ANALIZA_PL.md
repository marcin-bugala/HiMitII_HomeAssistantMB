# Hi-Mit II MB — zakres rozszerzenia

Baza: `marcin-bugala/HiMitII_HomeAssistantMB`, commit
`dbe2f6e6fbd8e9833d7fca7b5f5cfecfc905389e`. Aktualna wersja rozszerzenia: 1.3.0.
Przeanalizowano oryginalny plik diagnostyczny przekazany w poprzednim czacie.
W testach pozostawiono wyłącznie anonimową telemetrię; nie ma danych konta,
identyfikatorów urządzenia ani czasu zrzutu.

## Źródła i poziomy pewności

- [Kod integracji](https://github.com/danardelean/HiMitII_HomeAssistant) definiuje
  pobieranie i łączenie `allStatus`, `functions`, `status`. Ostatnia grupa ma
  pierwszeństwo. Nowe encje korzystają z tego samego odczytu.
- [PR #1 autorstwa elektron81](https://github.com/danardelean/HiMitII_HomeAssistant/pull/1)
  jest źródłem poprawek logowania oraz polskiego tłumaczenia. Uwzględniono stan
  `6ffa48d5e1f6c8e733ea879eafcc91289b0f9181`, wraz z HACS i nazwami encji.
  Adresy repozytorium dostosowano do forka MB. Usunięto błędy wcięć, podwójne
  wywołanie odczytu i nieosiągalny kod obecne w bazowym forku MB.
- [Instrukcja Hi-Mit, str. 29–32](https://app-resources.hijuconn.com/himit-web/doc/wsde9ddfhe53feer/Hi-Mit_app_instructions.pdf)
  opisuje tryby, ECO, tryb cichy, nocny i alarmy, ale nie podaje mapowania JSON.
- [Badania protokołu H-NET](https://github.com/alex89rm/Hisense-H-NET-Protocol/blob/main/docs/Remote_controller_interface.md)
  opisują m.in. defrost, częstotliwość, PWM i przepływ. Część opisów jest oznaczona
  jako niepotwierdzona. Nie dowodzą one, że pole chmurowe o podobnej nazwie ma tę
  samą skalę lub semantykę.

**Potwierdzone:** obecność poniższych pól w zrzucie, ich reprezentacja i poprawne
udostępnienie w encjach. **Eksperymentalne:** znaczenie flag, ich polaryzacja
podczas rzeczywistego zdarzenia i wsparcie danego modelu. **Nieustalone:** słowniki
trybów i alarmów, jednostki oraz przeliczniki telemetrii. Nie dodano COP ani
informacji o rzeczywistej pracy sprężarki.

## Nowe encje

Domyślnie włączone jako zwykłe sensory są cztery pola okresowe:
`Power_heating`, `Capacity_heating`, `Power_DHW`, `Capacity_DHW`. Pozostałe 26
encji jest diagnostycznych i domyślnie wyłączonych w nowych instalacjach. Aktualizacja
zachowuje wszystkie już włączone encje i ręczne wyłączenia użytkownika; nie
przerywa istniejącej rejestracji. Automatycznie włącza tylko cztery sensory,
jeśli wyłączyły je starsze ustawienia domyślne integracji. Status eksperymentalny
mapowań pozostaje bez zmian. Każda dodana encja wskazuje pole źródłowe i poziom pewności w atrybutach
`source_field` oraz `mapping_confidence`.

| Pole API | Interpretacja robocza | Udostępnienie |
|---|---|---|
| `Defrost_Spaceheat_s` | Odszranianie CO | Eksperymentalna flaga |
| `Defrost_DHW_s` | Odszranianie CWU | Eksperymentalna flaga |
| `Antifrozen_HP_s` | Ochrona przeciwzamrożeniowa pompy ciepła | Eksperymentalna flaga |
| `1_Antifrozen_WP1_s`, `2_Antifrozen_WP1_s` | Dwie flagi ochrony pompy obiegowej | Eksperymentalne flagi |
| `Antifrozen_EH1_s` | Ochrona przeciwzamrożeniowa grzałki | Eksperymentalna flaga |
| `isECO`, `isNightMode`, `isSilentMode` | ECO, nocny, cichy | Eksperymentalne flagi |
| `isEleHeatingTurnon` | Flaga grzania elektrycznego; nie dowodzi poboru mocy | Eksperymentalna flaga |
| `isDisinfect`, `Anti_Legionella_s` | Flagi dezynfekcji; nie łączymy ich w jedną | Eksperymentalne flagi |
| `DHW_Boost_s`, `Emergency_Mode_s` | Boost CWU, tryb awaryjny | Eksperymentalne flagi |
| `alarmCode` | Kod alarmu, bez opisu ani wyliczonej flagi alarmu | Surowy tekst |
| `realRunMode`, `mode` | Kody trybów, bez etykiet ogrzewanie/chłodzenie/postój | Surowy tekst |
| `Twi`, `Two`, `Twohp` | Możliwe temperatury wody | Surowy tekst, bez jednostki |
| `Pw`, `PWM`, `Fd`, `Q_p` | Możliwe parametry hydrauliki i sprężarki | Surowy tekst, bez jednostki |
| `Power_heating`, `Capacity_heating`, `Power_DHW`, `Capacity_DHW` | Parametry energetyczne o nieznanej skali | Surowy tekst, bez jednostki |
| `EH1_Power`, `EH2_Power` | Parametry grzałek o nieznanej skali | Surowy tekst, bez jednostki |

Łącznie: 14 nowych czujników binarnych i 16 czujników tekstowych.
W zrzucie flagi mają wartość `0`; telemetria dodatkowa także zawiera wartości zerowe.
Nie rozstrzygamy, czy są rzeczywistymi odczytami, wartościami domyślnymi lub
parametrami nieobsługiwanymi. Zero pozostaje widoczne.

Dekoder binarny przyjmuje tylko jawne 0/1 i true/false. Brak pola, null lub
nieznana wartość powoduje niedostępność encji. Błąd aktualizacji koordynatora
również powoduje niedostępność. Tekst `"0"` nie jest traktowany jak prawda.
Nie dodano klas statystyk ani jednostek, które mogłyby wprowadzić niepewne dane
do panelu energii.

## Kompatybilność i bezpieczeństwo

Pozostają domena `himit`, klucze, unikalne identyfikatory i przypisanie urządzeń.
Nie zmieniono komend istniejących przełączników i nastaw. Nazwy są tłumaczone
zgodnie z PR #1; istniejące identyfikatory z rejestru HA pozostają zachowane.
Nowo tworzone identyfikatory mogą zależeć od języka HA.

Encja `a2w_running` nadal czyta `A2W_SW_ON`, aby nie zmieniać automatyzacji.
Jej nazwa to teraz „Pompa ciepła włączona”, bez klasy urządzenia RUNNING.
Pole oznacza włączenie główne i nie potwierdza pracy sprężarki. Atrybut
`compressor_running_verified: false` wskazuje to ograniczenie.

Nie dodano endpointów, dodatkowego odpytywania ani nowych operacji sterowania.
Nie logowano się do chmury użytkownika i nie wysyłano komend do pompy.
Istniejące sterowanie w integracji pozostaje dostępne po instalacji.
Eksport diagnostyki maskuje więcej pól, także wewnętrznych, a identyfikatory
użyte jako klucze `device_states` zastępuje przez `device_1`, itd.
Nieznane pola producenta nadal wymagają sprawdzenia przed publicznym udostępnieniem.

## Weryfikacja

Testy offline obejmują rzeczywiste klasy encji HA, anonimowy zrzut, zmiany 0→1,
brakujące i nieprawidłowe dane, awarie koordynatora, pierwszeństwo grup API,
zachowanie identyfikatorów, kompletność PL/EN oraz redakcję diagnostyki.
Testy logowania sprawdzają odświeżenie, fallback po `HimitAPIError` (w tym kod 1),
HTTP 401/403, pojedynczą próbę ponownego logowania, limit prób i rozróżnienie
błędów sieci od uwierzytelnienia. Zapis tokenu nie przeładowuje integracji;
zmiana opcji ją przeładowuje.

Środowisko wykonanych testów: Python 3.12.14, klasy Home Assistant 2024.3.3 na
Windows. Nie jest to test uruchomienia pełnego HA OS ani test na wersji
2026.10.4 użytkownika. Testy używają atrap klienta API i obiektu HA, bez sieci.

## Instalacja i dalsza walidacja

1. Wykonać kopię aktualnego katalogu `custom_components/himit`.
2. Zastąpić go katalogiem z przygotowanej paczki i uruchomić ponownie HA.
   Nie usuwać konfiguracji integracji ani jej encji.
3. Sprawdzić dostępność czterech sensorów okresowych. Pozostałe odczyty można
   włączyć w rejestrze encji do dalszej walidacji. Już włączone pozostają aktywne.
4. Porównać obserwacje z kontrolerem i aplikacją podczas naturalnego postoju,
   CO, CWU oraz odszraniania. Zapisać czas, stan na kontrolerze i zrzut diagnostyki.
5. Do potwierdzenia mapowania wymagać zgodności przed, podczas i po zdarzeniu,
   najlepiej dla kilku cykli. Nie wymuszać odszraniania ani grzałek na potrzeby testu.
6. Obserwować ciągłość danych przez co najmniej jeden okres ważności tokenu.

W razie problemów przywrócić poprzedni katalog i ponownie uruchomić HA.
Odczyty chmurowe co 30 sekund mogą pomijać krótkie zdarzenia. Flagi eksperymentalne
nie powinny być jedynym zabezpieczeniem odpływu skroplin.

Endpointy `get_atw_vales` i `get_hmt_attr_info` pozostają kolejnym etapem:
przed implementacją potrzebne są ich zanonimizowane odpowiedzi oraz potwierdzenie
formatu. Aktualne dane wystarczają do tej wersji bez rozszerzania komunikacji.

## Weryfikacja historii 6–10 listopada 2026

Na obserwowanej instalacji przeanalizowano około 95 godzin historii wszystkich
30 dodatków, od 6 listopada około 19:12 do 10 listopada około 17:53 czasu Polski.
Zmienne były cztery pola:

| Pole | Zakres | Liczba zmian po początku wspólnego okna |
|---|---|---|
| `Power_heating` | 0–6 | 24 |
| `Capacity_heating` | 0–22 | 49 |
| `Power_DHW` | 0–9 | 31 |
| `Capacity_DHW` | 0–20 | 32 |

Suma pól Power porównana z 576 pięciominutowymi średnimi licznika w oknie
8 listopada 17:50 — 10 listopada 17:50 miała korelację około 0,31 bez
przesunięcia oraz około 0,84 przy opóźnieniu danych chmurowych o 30 minut.
To opis tej próby, nie walidacja protokołu dla wszystkich modeli. Sugeruje dane
za miniony okres. Nie dowodzi dokładnej długości okresu, jednostki ani skali.

Przykład: 10 listopada o 15:39 `Power_heating=2` i `Power_DHW=7`, a całka
pięciominutowej mocy licznika za poprzednie 30 minut wynosiła około 0,96 kWh.
Hipoteza 0,1 kWh na jednostkę jest interesująca, lecz rozbieżności innych
przedziałów nie pozwalają wdrożyć tego przelicznika. **W kodzie nie ma
konwersji do kW/kWh, przesuwania znaczników czasu, sumowania energii ani COP.**

Wszystkie 14 flag pozostało `off`, a 12 pozostałych surowych pól pozostało
zerowych. Brak aktywacji alarmu czy grzałki może być prawidłowy; nie oznaczamy
tych pól jako nieobsługiwane. Defrost nie uzyskał niezależnego potwierdzenia.

Osiem odczytów `TsR1`–`TsR8` pozostawało 22°C. Są teraz opisane jako
niezweryfikowane i domyślnie wyłączone diagnostycznie dla nowych instalacji.
Istniejące wartości, jednostki, klasy statystyk i identyfikatory zachowano.

Surowe sensory mają `data_role`: `periodic_unverified` dla czterech kandydatów
i `auxiliary_unverified` dla pozostałych. `source_field` i `mapping_confidence`
pozostają kompatybilne. Nowe pola mają `suitable_for_realtime_control: false`;
cztery sensory okresowe również `unit_scale_verified: false` i
`period_verified: false`. Oznacza to brak walidacji, nie automatyczną blokadę
użycia encji przez automatyzacje HA.
