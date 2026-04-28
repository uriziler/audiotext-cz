# Specifikace projektu v0.1

## Název projektu

AudioText CZ

## Stručný popis

AudioText CZ je Android aplikace pro lokální přepis audio nahrávek do textu. Uživatel nahraje existující audio soubor, zvolí lokální Whisper model a aplikace vytvoří český textový přepis bez odesílání audia do cloudu.

MVP cílí primárně na Samsung S25 Ultra a používá češtinu jako výchozí jazyk.

## Cíl produktu

Cílem je umožnit rychlý a soukromý přepis osobních nahrávek přímo v telefonu. Aplikace má být jednoduchá, offline použitelná a připravená na delší nahrávky, které se nevejdou do krátkého diktovacího scénáře.

Produkt řeší hlavně tyto potřeby:

- přepsat schůzku, poznámku, rozhovor nebo hlasový záznam do textu
- udržet audio i přepis pouze v zařízení
- mít možnost zvolit kompromis mezi rychlostí a přesností
- uložit přepis a později se k němu vrátit

## Cíloví uživatelé

- Hlavní uživatel: člověk, který má na telefonu audio nahrávky a chce z nich získat český text.
- Technicky středně zdatný uživatel: zvládne vybrat soubor, stáhnout model a počkat na lokální zpracování.
- První cílové zařízení: Samsung S25 Ultra.

## Hlavní scénáře použití

- Jako uživatel chci vybrat audio soubor z telefonu, abych ho mohl přepsat do textu.
- Jako uživatel chci stáhnout lokální model, abych mohl přepisovat offline.
- Jako uživatel chci vybrat model Base, Small, Medium nebo Large, abych si zvolil rychlost a kvalitu přepisu.
- Jako uživatel chci mít češtinu jako výchozí jazyk, abych nemusel pokaždé nastavovat jazyk přepisu.
- Jako uživatel chci vidět průběh přepisu, abych věděl, že dlouhá úloha běží.
- Jako uživatel chci vidět přepis po časovaných segmentech, abych se v něm lépe orientoval.
- Jako uživatel chci upravit text přepisu, abych mohl opravit chyby modelu.
- Jako uživatel chci exportovat přepis do TXT, abych ho mohl použít mimo aplikaci.

## Funkční požadavky

- Aplikace musí umožnit import existujícího audio souboru.
- Aplikace musí uložit nahrávku jako lokální záznam v seznamu nahrávek.
- Aplikace musí evidovat stav nahrávky: importováno, příprava audia, čeká na model, přepisuje se, hotovo, chyba.
- Aplikace musí umožnit stažení lokálních modelů Base, Small, Medium a Large.
- Aplikace musí zobrazit, které modely jsou stažené a které chybí.
- Aplikace musí umožnit smazání staženého modelu.
- Aplikace musí umožnit vybrat model pro přepis.
- Aplikace musí používat češtinu jako výchozí jazyk přepisu.
- Aplikace musí spustit lokální přepis pomocí `whisper.cpp`.
- Aplikace musí zpracovat přepis na pozadí a zobrazovat průběžný stav.
- Aplikace musí uložit výsledné segmenty přepisu do lokální databáze.
- Aplikace musí zobrazit detail nahrávky s výsledným textem.
- Aplikace musí umožnit editaci textu jednotlivých segmentů.
- Aplikace musí umožnit export celého přepisu do TXT.
- Aplikace musí zobrazit srozumitelnou chybu, pokud audio nejde přečíst, model chybí nebo přepis selže.

## Nefunkční požadavky

- MVP musí fungovat offline po stažení modelu.
- Audio se v MVP nesmí odesílat do cloudové služby.
- Rozhraní aplikace bude v češtině.
- Výchozí jazyk přepisu je čeština, interně `cs`.
- Aplikace musí zvládat dlouho běžící přepis bez pádu UI.
- Aplikace musí během dlouhého přepisu používat foreground/background mechanismus vhodný pro Android.
- Aplikace musí držet v paměti vždy jen jeden Whisper model.
- Aplikace musí ukládat data lokálně do interního app storage a Room databáze.
- Aplikace musí pracovat bezpečně s velkými modelovými soubory a nedávat je do APK.
- Aplikace musí mít jasné chybové stavy místo tichého selhání.

## Pracovní defaulty

- MVP umí pouze import existujícího audio souboru, ne vlastní nahrávání.
- Podporované vstupy v MVP: `m4a`, `mp3`, `wav`, pokud je zvládne Android media stack.
- Výchozí model: Small.
- Base je lehčí režim pod Small pro rychlý test nebo úsporu.
- Large v MVP znamená `large-v3-turbo-q5_0`.
- TXT je jediný export v MVP.
- Originální audio se ponechává, dokud uživatel nesmaže nahrávku.
- Pracovní převedené audio se po úspěšném přepisu maže.
- Modely se stahují v aplikaci, ideálně přes Wi-Fi; mobilní data vyžadují potvrzení.
- Package name: `cz.local.audiotextcz`, pokud ho později nezměníme.

## Rozsah MVP

- Import audio souboru.
- Seznam nahrávek.
- Detail nahrávky.
- Lokální databáze nahrávek a segmentů.
- Model manager pro Base, Small, Medium a Large.
- Lokální přepis přes `whisper.cpp`.
- Čeština jako výchozí jazyk.
- Zobrazení segmentovaného přepisu.
- Editace textu segmentů.
- Export do TXT.
- Základní chybové stavy.

## Mimo scope

- Cloud transcription.
- Login a uživatelské účty.
- Synchronizace mezi zařízeními.
- Realtime přepis při nahrávání.
- Vlastní nahrávání audia v první verzi.
- Diarizace mluvčích.
- Shrnutí přepisu.
- Překlad do jiných jazyků.
- SRT/VTT export.
- Sdílení databáze mezi zařízeními.
- Pokročilý editor textu.

## Akceptační kritéria

- Uživatel otevře aplikaci a vidí seznam nahrávek.
- Uživatel importuje audio soubor a v seznamu vznikne nový záznam.
- Uživatel vidí stav modelů Base, Small, Medium a Large.
- Uživatel stáhne vybraný model a aplikace ho označí jako připravený.
- Uživatel spustí přepis s modelem Base, Small, Medium nebo Large.
- Přepis používá jazyk `cs`, pokud uživatel neudělá pozdější změnu nastavení.
- Přepis běží mimo hlavní UI thread.
- Po dokončení přepisu aplikace zobrazí segmentovaný text.
- Uživatel upraví text segmentu a změna zůstane uložená po restartu aplikace.
- Uživatel exportuje přepis do TXT.
- Pokud model chybí, aplikace nabídne jeho stažení místo pádu.
- Pokud audio nejde dekódovat, aplikace zobrazí srozumitelnou chybu.
- Pokud přepis selže, stav nahrávky je `failed` a chyba je viditelná v UI.

## Otevřené otázky a rizika

- Minimální Android verze ještě není finálně potvrzená.
- Přesné download URL a checksums modelů se doplní před implementací Model Manageru.
- Výkon modelů Medium a Large na S25 Ultra je nutné změřit na reálném zařízení.
- Android media stack nemusí zvládnout všechny varianty audio souborů, zejména okrajové kodeky.
- `whisper.cpp` integrace přes NDK může vyžadovat samostatný technický spike.
- Dlouhé nahrávky mohou vyžadovat chunking a opatrné nakládání s pamětí.
- Stahování velkých modelů musí mít obnovitelnost nebo jasnou chybovou cestu.
