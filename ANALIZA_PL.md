# Hi-Mit II MB — zakres rozszerzenia

Baza: `marcin-bugala/HiMitII_HomeAssistantMB`, commit
`dbe2f6e6fbd8e9833d7fca7b5f5cfecfc905389e`. Wersja lokalnego rozszerzenia: 1.2.0.
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

Wszystkie mają kategorię diagnostyczną. Jedynie surowy kod alarmu jest domyślnie
włączony. Każda dodana encja wskazuje pole źródłowe i poziom pewności w atrybutach
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
Jej dotychczasowa nazwa sugeruje pracę, ale pole oznacza włączenie główne i nie
potwierdza pracy sprężarki. Nie używać go jako dowodu pracy sprężarki.

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
3. Włączyć wybrane encje diagnostyczne w rejestrze encji HA.
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
