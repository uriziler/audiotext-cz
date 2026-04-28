# Workflow pro návrh a vývoj větší aplikace

Tento dokument je pracovní manuál pro návrh a výrobu větší aplikace. Slouží jako mantinel pro člověka i AI: drží kontext, odděluje fáze, chrání hranice modulů a snižuje riziko, že se projekt postupně rozjede do chaosu.

## Fáze

1. Specifikace
2. Architektura
3. Datový model
4. API design
5. Implementace modulů
6. Testování
7. Refactoring

## Specifikace

### Cíl

Popsat, co přesně má vzniknout, pro koho to je, jaký problém to řeší a co je součást první verze.

Specifikace je fáze, kde se ještě neřeší kód. Řeší se, co systém má dělat, ne jak bude implementovaný. U vibe codingu je to kritické, protože když je specifikace vágní, AI začne domýšlet věci sama a projekt se rozjede do chaosu.

### Co má být výstupem

- co se staví
- pro koho se to staví
- jaký problém to řeší
- co musí umět v první verzi
- co ještě dělat nemá
- jak poznáš, že je hotovo

### Co sledovat

- příliš obecné zadání
- smíchané zadání a technické řešení
- nejasné role uživatelů
- nejasné MVP
- chybějící out-of-scope
- chybějící akceptační kritéria
- otevřené otázky, které nikdo nepojmenoval

### Struktura specifikace

- Název a stručný popis
- Cíl produktu
- Cíloví uživatelé
- Hlavní scénáře použití / user stories
- Funkční požadavky
- Nefunkční požadavky
- Rozsah MVP
- Mimo scope
- Akceptační kritéria
- Otevřené otázky a rizika

### Pravidla

- neřešit zde technologii, framework ani konkrétní implementaci
- popisovat chování systému, ne technické detaily řešení
- oddělit MVP od nice-to-have
- explicitně zapsat, co je mimo scope
- každou důležitou funkci formulovat tak, aby šla otestovat
- přiznat nejasnosti místo toho, aby se skryly

### Šablona výstupu

```markdown
# Specifikace projektu

## Název projektu
[Doplň]

## Stručný popis
[Doplň 2-3 věty o tom, co aplikace dělá]

## Cíl produktu
[Doplň, jaký problém řeší a proč vzniká]

## Cíloví uživatelé
- [uživatel 1]
- [uživatel 2]

## Hlavní scénáře použití
- Jako [typ uživatele] chci [akce], abych [výsledek].
- Jako [typ uživatele] chci [akce], abych [výsledek].

## Funkční požadavky
- Systém musí umožnit ...
- Uživatel může ...
- Administrátor může ...

## Nefunkční požadavky
- Aplikace musí fungovat na ...
- Přístup musí být omezen ...
- Rozhraní bude v jazyce ...

## Rozsah MVP
- [funkce 1]
- [funkce 2]
- [funkce 3]

## Mimo scope
- [věc 1]
- [věc 2]

## Akceptační kritéria
- Funkce je hotová, pokud ...
- Funkce je hotová, pokud ...

## Otevřené otázky a rizika
- [otázka 1]
- [riziko 1]
```

## Architektura

### Cíl

Rozhodnout, z jakých částí se systém skládá a jak spolu komunikují.

Specifikace říká co. Architektura říká, jak to bude poskládané. Tady se ještě pořád neřeší konkrétní kód. Řeší se struktura systému, moduly, vrstvy, hranice a tok dat.

### Co má být výstupem

- typ architektury
- hlavní části systému
- moduly
- odpovědnosti jednotlivých částí
- vztahy mezi nimi
- tok dat
- role a oprávnění
- externí závislosti
- architektonická pravidla
- otevřená rozhodnutí

### Co sledovat

- nejasné hranice mezi moduly
- příliš mnoho technologií
- byznys logika v UI
- neoddělená integrační vrstva
- nejasný vlastník dat a pravidel
- moduly, které sahají všude
- architektura chytřejší než problém

### Typ architektury

Pro většinu větších vibe-coding projektů bývá nejlepší modulární monolit:

- jedna aplikace
- jedna codebase
- jedna databáze
- logické rozdělení do modulů

### Co typicky řeší architektura

- Typ architektury
- Hlavní části systému
- Moduly
- Tok dat
- Role a oprávnění
- Externí integrace

### Pravidla

- držet architekturu jednoduchou
- preferovat modulární monolit před mikroservisami, pokud není silný důvod jinak
- každý modul musí mít jasnou odpovědnost
- UI nesmí obsahovat hlavní business logiku
- validace a oprávnění musí být v backendu, pokud backend existuje
- integrace držet oddělené od jádra systému
- architektura má odrážet doménu problému, ne layout obrazovek

### Šablona výstupu

```markdown
# Architektura systému

## Typ architektury
[Doplň: monolit / modulární monolit / více služeb]

## Hlavní části systému
- [část 1]
- [část 2]
- [část 3]

## Moduly

### Modul: [název]
- Odpovědnost:
- Vstupy:
- Výstupy:
- Závislosti:

### Modul: [název]
- Odpovědnost:
- Vstupy:
- Výstupy:
- Závislosti:

## Tok dat
1. [krok 1]
2. [krok 2]
3. [krok 3]

## Role a oprávnění
- [role 1]: [co smí]
- [role 2]: [co smí]

## Externí integrace
- [služba]: [účel], [riziko při výpadku]

## Architektonická pravidla
- UI neobsahuje byznys logiku
- Validace je centralizovaná
- Přístup k datům jde přes jasně určenou vrstvu
- Moduly komunikují přes definovaná rozhraní

## Otevřená rozhodnutí
- [otázka 1]
- [otázka 2]
```

## Datový model

### Cíl

Popsat, jaká data systém má a jak spolu souvisí.

Tady se dostáváme ke strukturám databáze a hlavním entitám systému, ale ještě neřešíme konkrétní SQL nebo ORM. Architektura říká, kdo co dělá. Datový model říká, co v datech existuje.

### Co má být výstupem

- seznam entit
- jejich atributy
- vztahy mezi nimi
- vlastnictví dat
- zdroj pravdy
- pravidla pro historii a změny
- rizikové body datového modelu

### Co sledovat

- nejasné entity
- chybějící vazby
- duplicitní data bez důvodu
- nejasný zdroj pravdy
- špatně řešená historie
- odvozená data uložená bez jasných pravidel
- model příliš navázaný na konkrétní UI

### Co datový model typicky obsahuje

- Entity
- Vztahy
- Historie a změny
- Zdroj pravdy
- Rizika a otevřené otázky

### Pravidla

- každá entita musí mít jasnou identitu
- data se mají ukládat tam, kde je jejich vlastník
- odvozená data ukládat jen tehdy, když je pro to důvod
- myslet na historii, audit a stabilitu výsledků
- nepřizpůsobovat model jen aktuálním obrazovkám
- být explicitní v tom, co je zdroj pravdy

### Šablona výstupu

```markdown
# Datový model

## Entities

### [Entity 1]
- id
- [atribut]
- [atribut]

### [Entity 2]
- id
- [atribut]
- [atribut]

## Relationships
- [Entity A] -> [Entity B]
- [Entity C] -> [Entity D]

## Source of truth
- [věc] vlastní [doména / entita]

## Historie a verze
- [jak řešit změny]

## Otevřená rozhodnutí
- [riziko]
- [otázka]
```

## API design

### Cíl

Navrhnout, jak spolu budou mluvit části systému, typicky frontend a backend.

API design je dohoda o tom:

- jaké existují zdroje
- jaké akce nad nimi děláš
- kdo je smí volat
- jak vypadají vstupy a výstupy
- jak se řeší chyby
- jak se řeší autorizace

### Co má být výstupem

- seznam endpointů
- rozdělení podle domén / zdrojů
- request a response kontrakty
- action endpointy
- pravidla autorizace
- error model
- základní pravidla konzistence

### Co sledovat

- endpointy navržené podle tlačítek místo domény
- nekonzistentní názvy
- unikající citlivá data
- business logika mimo správné místo
- různé chybové formáty
- duplicity v endpointovém návrhu
- response vracející víc, než má být

### Co API design typicky řeší

- Zdroje
- Action endpointy
- Role a oprávnění
- Chyby
- Konzistentní response model

### Pravidla

- API navrhovat podle doménových zdrojů, ne podle obrazovek
- akce typu publish, submit, approve mít jako action endpointy
- response nesmí vracet víc dat, než role potřebuje
- držet konzistentní naming
- mít jednotný error model
- business pravidla nesmí být roztříštěná mezi více endpointů bez důvodu

### Šablona výstupu

```markdown
# API design

## [Doména / resource]
- GET /resource
- GET /resource/{id}
- POST /resource
- PATCH /resource/{id}
- DELETE /resource/{id}

## Action endpoints
- POST /resource/{id}/action

## API pravidla
- API se navrhuje podle doménových zdrojů
- Byznys akce mají vlastní action endpointy
- Oprávnění se kontrolují na backendu
- Response nesmí vracet citlivá data nepovoleným rolím
- Chybové stavy mají konzistentní strukturu
```

## Implementace modulů

### Cíl

Převést návrh do kódu tak, aby architektura zůstala zachovaná.

Tady už se píše kód, ale ne bezhlavě. Neimplementuje se všechno najednou. Postupuje se po modulech a vrstvách.

### Co má být výstupem

- implementované entity / modely
- datová vrstva
- business logika
- API controllery
- frontend napojený na backend
- základní technická kostra projektu
- zachované vrstvy a hranice

### Co sledovat

- logika nacpaná do controllerů
- SQL / ORM chaos rozesetý po kódu
- míchání vrstev
- AI generující vše do jednoho souboru
- nejasná struktura složek
- porušení architektury během implementace
- nehlídané závislosti mezi moduly

### Doporučené pořadí implementace

1. modely / entity
2. repository / data access
3. services / business logika
4. controllers / API vrstva
5. frontend

### Typické vrstvy

- model / entity
- repository
- service
- controller
- frontend

### Pravidla

- controller má být tenký
- service má obsahovat business logiku
- repository má řešit data
- frontend nesmí být zdroj pravdy
- implementovat po malých blocích
- držet strukturu projektu podle domén a vrstev
- nové feature nepsat bez kontextu architektury

### Šablona výstupu

```markdown
# Implementační strategie

## Pořadí implementace modulů
1. [modul 1]
2. [modul 2]
3. [modul 3]

## Architektonické vrstvy
1. Models / Entities
2. Repository / Data access
3. Services / Business logic
4. Controllers / API
5. Frontend / Presentation

## Implementační pravidla
- Controller obsahuje pouze HTTP logiku
- Business logika je ve service vrstvě
- Databázový přístup je v repository
- Moduly mají jasně oddělené odpovědnosti
- Endpointy odpovídají návrhu API
```

## Testování

### Cíl

Ověřit, že systém funguje podle specifikace a že změny nerozbíjejí existující chování.

U většího vibe codingu je testování zásadní, protože AI umí rychle vyrobit funkční kód, ale stejně rychle umí přinést regresi, nekonzistenci a skryté chyby.

### Co má být výstupem

- testovací strategie
- unit testy kritické logiky
- integrační testy hlavních toků
- e2e testy klíčových scénářů
- pokrytí hlavních edge cases
- jistota pro další vývoj a refactoring

### Co sledovat

- testování implementation details místo chování
- chybějící edge cases
- absence testů kolem kritických flow
- křehké testy
- testy dopsané příliš pozdě
- netestovaná oprávnění
- netestované chybové stavy

### Typy testů

- Unit testy: testují malý kus logiky izolovaně.
- Integrační testy: testují spolupráci více částí systému.
- End-to-end testy: testují celé hlavní flow z pohledu uživatele.

### Pravidla

- testovat hlavně kritické byznys flow
- testovat chování, ne vnitřní implementaci
- pokrýt i chybové a hraniční stavy
- psát testy průběžně, ne až na konec
- používat testovací pyramidu: hodně unit, méně integration, pár e2e
- chránit hlavně moduly s nejvyšším rizikem změn

### Šablona výstupu

```markdown
# Testovací strategie

## Typy testů
- Unit testy
- Integrační testy
- End-to-end testy

## Priority testování
1. Kritické business flow
2. Oprávnění a bezpečnost
3. Složitá logika
4. Edge cases
5. Regrese

## Co testovat
- Vyhodnocení
- Počet povolených pokusů
- Odevzdání / potvrzení procesů
- Přístupová práva
- Reporting / výsledky

## Pravidla
- Testovat chování, ne interní implementaci
- Pokrýt i chybové a hraniční stavy
- Psát testy průběžně s implementací
```

## Refactoring

### Cíl

Zlepšit vnitřní strukturu kódu bez změny externího chování.

Refactoring je fáze, kdy systém už funguje, ale upravuje se jeho vnitřní struktura tak, aby byl:

- čitelnější
- jednodušší
- méně křehký
- lépe rozšiřitelný
- snáz testovatelný

### Co má být výstupem

- čistší struktura kódu
- menší duplicita
- jasnější názvy
- oddělené odpovědnosti
- narovnané závislosti
- sjednocené chybové stavy
- udržitelnější modulární návrh

### Kdy refaktorovat

- po dokončení modulu
- před větším rozšířením
- po sérii rychlých AI změn
- při výskytu code smells

### Co sledovat

- dlouhé metody
- duplicity
- špatné názvy
- míchání odpovědností
- silné závislosti
- nekonzistentní chybové stavy
- chaos ve stavech a pravidlech

### Co se typicky refaktoruje

- struktura metod a funkcí
- rozdělení odpovědností
- duplicity
- názvy
- datové struktury
- závislosti
- chybové modely

### Pravidla

- refaktorovat v malých krocích
- chránit změny testy
- neměnit externí chování bez záměru
- přesouvat logiku do správných vrstev
- sjednocovat názvy, stavy a error model

### Šablona výstupu

```markdown
# Refactoring - pravidla

## Cíl
Zlepšit vnitřní strukturu kódu bez změny externího chování.

## Kdy refaktorovat
- po dokončení modulu
- před větším rozšířením
- po sérii rychlých AI změn
- při výskytu code smells

## Co sledovat
- dlouhé metody
- duplicity
- špatné názvy
- míchání odpovědností
- silné závislosti
- nekonzistentní chybové stavy
- chaos ve stavech a pravidlech

## Pravidla
- refaktorovat v malých krocích
- chránit změny testy
- neměnit externí chování bez záměru
- přesouvat logiku do správných vrstev
- sjednocovat názvy, stavy a error model
```

## Průřezové pojmy

### Domény

Doména je oblast problému, kterou systém řeší. Doména není technologie ani stránka webu. Je to oblast problému se svými pravidly a daty.

Příklady:

- Identity
- Booking
- Leads
- Quiz management
- Evaluation
- Reporting

### Entity

Entita je hlavní objekt systému, který má identitu a existuje v čase.

Entity mají:

- identitu
- data
- životní cyklus

### Vlastník pravdy

Každá důležitá věc v systému má mít jasného vlastníka.

Příklad:

- otázky vlastní Quiz doména
- odpovědi vlastní Execution
- skóre vlastní Evaluation
- statistiky vlastní Reporting

Tohle drží konzistenci systému.

### DDD lite

Jednoduché použití principu Domain-Driven Design bez přehnané složitosti.

Cíl:

- rozdělit systém na domény
- držet hranice
- zabránit chaosu ve větších projektech

Základní pravidla:

- každá doména vlastní svá data a pravidla
- jiné domény jí do toho nesahají napřímo
- výsledky se nepočítají na více místech různě
- tok závislostí má být čitelný a jednosměrný

### Vrstvy

Typické vrstvy aplikace:

- Frontend / Presentation
- Controller / API
- Service / Business logic
- Repository / Data access
- Model / Entity

Pravidlo:

- frontend nezajišťuje business pravdu
- controller je tenký
- service rozhoduje
- repository ukládá
- model reprezentuje data

### Master context

Dokument, který drží AI i člověka v mantinelech projektu.

Typicky obsahuje:

- specifikaci
- architekturu
- datový model
- API design
- domény
- implementační pravidla
- testovací pravidla

Použití:

- přikládáš ho při generování dalšího kódu
- kontroluješ proti němu nové změny
- vracíš se k němu, když se projekt začne rozpadat

### Doporučený master context

```markdown
# PROJECT_CONTEXT

## Cíl projektu
[Co má systém dělat]

## Cíloví uživatelé
- [uživatel 1]
- [uživatel 2]

## Domény
- [doména 1]
- [doména 2]
- [doména 3]

## Hlavní entity
- [entity 1]
- [entity 2]
- [entity 3]

## Zdroj pravdy
- [věc] vlastní [doména]

## Typ architektury
- modulární monolit

## Moduly
- [modul 1]
- [modul 2]
- [modul 3]

## Datový model
- [shrnutí entit a vztahů]

## API
- [hlavní endpointy]

## Implementační pravidla
- Controller je tenký
- Business logika je ve service vrstvě
- Repository řeší přístup k datům
- Frontend není zdroj pravdy

## Testovací pravidla
- Kritické flow musí mít testy
- Oprávnění se testují
- Refactoring je chráněný testy

## Refactoring pravidla
- malé kroky
- bez změny externího chování
- sjednocovat názvy, stavy a error model
```

## Jednoduchý tahák: co kam patří

- Specifikace: co to má dělat a pro koho.
- Architektura: z čeho se to skládá a jak to drží pohromadě.
- Datový model: jaká data existují a jak souvisí.
- API design: jak spolu části systému komunikují.
- Implementace: jak se to převádí do kódu.
- Testování: jak ověřit, že to funguje a nerozbíjí se.
- Refactoring: jak udržet systém čistý a rozšiřitelný.

## Hlavní meta-pravidlo pro větší vibe coding

Jakmile projekt roste, největší problém není, že AI neumí psát kód, ale:

- že zapomíná kontext
- že začne improvizovat strukturu
- že míchá odpovědnosti
- že duplikuje pravidla
- že rozbije hranice domén

Proto je tenhle workflow důležitý. Nechrání před každou chybou, ale chrání před tím nejhorším: aby se z funkčního projektu stal neudržitelný chaos.
