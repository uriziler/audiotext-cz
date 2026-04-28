# Datový model v0.1

## Cíl

Datový model popisuje, jaká data AudioText CZ ukládá lokálně, kdo je vlastní a jak spolu souvisí. MVP používá jednu lokální Room databázi a interní app storage pro audio a modelové soubory.

Databáze drží metadata, stavy a textové segmenty. Velké binární soubory se neukládají do databáze, ale do interního souborového úložiště.

## Konvence

- Primární ID jsou `String` UUID, pokud nebude při implementaci silný důvod pro `Long`.
- Časy jsou `Long` v epoch millis.
- Délky audia a segmentů jsou `Long` v milisekundách.
- Enumy se v Room ukládají jako stabilní `String`, ne ordinal.
- Cesty k souborům jsou interní app paths, ne trvalé externí URI.
- Externí URI z Android pickeru se používá pouze při importu a není source of truth po zkopírování souboru.

## Persistentní entity

### Recording

Lokální záznam importované nahrávky.

Room tabulka: `recordings`

```text
id: String
title: String
originalFileName: String?
originalAudioPath: String
workingAudioPath: String?
mimeType: String?
sizeBytes: Long?
durationMs: Long?
languageCode: String
selectedModelId: String
lastTranscribedModelId: String?
status: RecordingStatus
createdAt: Long
updatedAt: Long
completedAt: Long?
errorCode: String?
errorMessage: String?
```

Poznámky:

- `originalAudioPath` je source of truth pro audio soubor po importu.
- `workingAudioPath` je dočasná pracovní verze audia pro přepis.
- `selectedModelId` říká, jaký model má uživatel pro nahrávku vybraný.
- `lastTranscribedModelId` říká, jakým modelem byl aktuální přepis skutečně vytvořen.
- `durationMs` může být `null`, dokud se metadata nepodaří načíst.

### TranscriptSegment

Jeden časovaný úsek přepisu.

Room tabulka: `transcript_segments`

```text
id: String
recordingId: String
segmentIndex: Int
startMs: Long
endMs: Long
text: String
isEdited: Boolean
createdAt: Long
updatedAt: Long
```

Poznámky:

- Segmenty se řadí podle `segmentIndex`, případně podle `startMs`.
- `isEdited` odlišuje text změněný uživatelem od surového výstupu modelu.
- Při novém přepisu stejné nahrávky se segmenty pro dané `recordingId` nahradí novou sadou, pokud uživatel výslovně potvrdí přepsání.

### LocalModel

Lokální stav jednoho podporovaného modelu.

Room tabulka: `local_models`

```text
id: String
displayName: String
fileName: String
downloadUrl: String
sha256: String
approximateSizeMb: Int
localPath: String?
status: ModelStatus
downloadedBytes: Long?
totalBytes: Long?
createdAt: Long
updatedAt: Long
errorCode: String?
errorMessage: String?
```

Poznámky:

- Katalog podporovaných modelů je definovaný v aplikaci.
- `local_models` ukládá aktuální stav na zařízení.
- `downloadUrl` a `sha256` jsou uložené kvůli diagnostice a migracím, ale zdroj definice je model catalog v kódu.
- `localPath` existuje pouze pro model ve stavu `ready`.

### TranscriptionJob

Stav jedné běžící nebo poslední transkripční úlohy.

Room tabulka: `transcription_jobs`

```text
id: String
recordingId: String
modelId: String
languageCode: String
status: TranscriptionJobStatus
progressPercent: Int
processedDurationMs: Long?
totalDurationMs: Long?
startedAt: Long?
finishedAt: Long?
createdAt: Long
updatedAt: Long
errorCode: String?
errorMessage: String?
```

Poznámky:

- MVP připouští maximálně jednu aktivní transkripční úlohu pro jednu nahrávku.
- Historii starších jobů můžeme ponechat pro diagnostiku, ale UI v MVP pracuje hlavně s posledním jobem.
- `progressPercent` je best-effort hodnota, protože reálný progress z `whisper.cpp` může být méně přesný u různých audio délek.

### AppSettings

Lokální nastavení aplikace.

Room tabulka nebo DataStore: `app_settings`

```text
id: String
defaultLanguageCode: String
defaultModelId: String
allowMobileDataForModelDownload: Boolean
keepOriginalAudio: Boolean
deleteWorkingAudioAfterSuccess: Boolean
createdAt: Long
updatedAt: Long
```

Výchozí hodnoty:

```text
defaultLanguageCode = "cs"
defaultModelId = "small"
allowMobileDataForModelDownload = false
keepOriginalAudio = true
deleteWorkingAudioAfterSuccess = true
```

Poznámky:

- AppSettings lze implementovat přes DataStore. Pokud zůstanou mimo Room, stále patří do datového modelu jako persistentní lokální data.

## Doménové a runtime objekty

Tyto objekty nemusí mít vlastní tabulku v MVP.

### WhisperModelDefinition

Definice modelu zabudovaná v aplikaci.

```text
id: String
displayName: String
qualityLabel: String
fileName: String
downloadUrl: String
sha256: String
approximateSizeMb: Int
recommendedUse: String
```

Příklady `id`:

```text
base
small
medium
large
```

### PreparedAudio

Výsledek přípravy audia pro přepis.

```text
recordingId: String
path: String
sampleRateHz: Int
channels: Int
durationMs: Long?
deleteAfterUse: Boolean
```

### TranscriptionRequest

Vstup do `TranscriptionEngine`.

```text
recordingId: String
audioPath: String
modelPath: String
modelId: String
languageCode: String
translate: Boolean
```

### TranscriptionResult

Výsledek lokálního enginu.

```text
segments: List<TranscriptSegmentDraft>
durationMs: Long?
engineInfo: String?
```

### TranscriptSegmentDraft

Segment před uložením do databáze.

```text
segmentIndex: Int
startMs: Long
endMs: Long
text: String
```

### ExportFile

Výsledek exportu.

```text
fileName: String
mimeType: String
pathOrUri: String
createdAt: Long
```

V MVP se export nemusí evidovat v databázi.

## Vztahy

- `Recording` má 0..n `TranscriptSegment`.
- `Recording` má 0..n `TranscriptionJob`.
- `Recording.selectedModelId` odkazuje na model id z katalogu.
- `Recording.lastTranscribedModelId` odkazuje na model id, kterým vznikly aktuální segmenty.
- `TranscriptSegment.recordingId` odkazuje na `Recording.id`.
- `TranscriptionJob.recordingId` odkazuje na `Recording.id`.
- `TranscriptionJob.modelId` odkazuje na model id z katalogu.
- `LocalModel.id` odpovídá model id z katalogu.
- `AppSettings.defaultModelId` odpovídá model id z katalogu.

## Source of truth

- Recording doména vlastní metadata nahrávky a stav nahrávky.
- TranscriptSegment data vlastní Transcription / Transcript doména.
- Model Management vlastní stav lokálních modelů.
- Model catalog v kódu vlastní seznam podporovaných modelů a jejich definice.
- AppSettings vlastní výchozí jazyk, výchozí model a download preference.
- FileStorage vlastní fyzické audio a modelové soubory.

## Stavy

### RecordingStatus

```text
imported
preparingAudio
waitingForModel
transcribing
completed
failed
```

Přechody:

- `imported -> waitingForModel`, pokud vybraný model není stažený.
- `imported -> preparingAudio`, pokud model existuje a uživatel spustí přepis.
- `waitingForModel -> preparingAudio`, po úspěšném stažení modelu a spuštění přepisu.
- `preparingAudio -> transcribing`, po přípravě audia.
- `transcribing -> completed`, po uložení segmentů.
- libovolný pracovní stav -> `failed`, pokud nastane chyba.

### ModelStatus

```text
notDownloaded
downloading
ready
failed
```

Přechody:

- `notDownloaded -> downloading`
- `downloading -> ready`
- `downloading -> failed`
- `failed -> downloading`
- `ready -> notDownloaded`, pokud uživatel model smaže.

### TranscriptionJobStatus

```text
queued
running
completed
failed
cancelled
```

Přechody:

- `queued -> running`
- `running -> completed`
- `running -> failed`
- `queued -> cancelled`
- `running -> cancelled`, pokud implementace dovolí přerušení.

## Indexy a constrainty

### recordings

- Primary key: `id`
- Index: `createdAt`
- Index: `status`
- Index: `selectedModelId`

### transcript_segments

- Primary key: `id`
- Foreign key: `recordingId -> recordings.id`
- Index: `recordingId`
- Unique index: `(recordingId, segmentIndex)`

### local_models

- Primary key: `id`
- Index: `status`

### transcription_jobs

- Primary key: `id`
- Foreign key: `recordingId -> recordings.id`
- Index: `recordingId`
- Index: `status`
- Index: `(recordingId, createdAt)`

## Mazání dat

### Smazání nahrávky

Při smazání `Recording`:

- smazat všechny `TranscriptSegment` pro danou nahrávku
- smazat nebo označit související `TranscriptionJob`
- smazat originální audio soubor, pokud existuje v app storage
- smazat working audio soubor, pokud existuje

### Smazání modelu

Při smazání `LocalModel` souboru:

- fyzicky smazat modelový soubor
- nastavit `localPath = null`
- nastavit `status = notDownloaded`
- nesmazat historické Recording záznamy, které tímto modelem vznikly

### Nový přepis existující nahrávky

Před přepsáním hotové nahrávky:

- UI musí upozornit, že aktuální segmenty budou nahrazeny
- po potvrzení smazat staré segmenty pro `recordingId`
- uložit nové segmenty
- aktualizovat `lastTranscribedModelId`

## Historie a verze

MVP neukládá plnou historii změn segmentů.

Ukládá se pouze:

- `isEdited`
- `updatedAt`
- model použitý pro aktuální přepis
- poslední error stav

Budoucí rozšíření:

- historie editací segmentů
- více verzí přepisu jedné nahrávky
- porovnání výsledků mezi modely
- SRT/VTT export historie

## Room schema v1

Schema v1 obsahuje:

- `recordings`
- `transcript_segments`
- `local_models`
- `transcription_jobs`
- volitelně `app_settings`, pokud nepoužijeme DataStore

Pravidla pro migrace:

- I v MVP zapnout export Room schema do repozitáře.
- Nepřejmenovávat enum hodnoty bez migrace.
- Nepoužívat ordinal enumy.
- Přidávání nullable sloupců je preferovaná cesta pro malé evoluce.
- Větší změny zapisovat do samostatného migračního dokumentu.

## Otevřená rozhodnutí

- Jestli AppSettings bude v Room, nebo DataStore.
- Jestli `TranscriptionJob` bude držet historii všech jobů, nebo jen poslední job na Recording.
- Přesné hodnoty `errorCode`.
- Jestli budeme ukládat token-level metadata z Whisperu. MVP s tím nepočítá.
- Jestli `durationMs` spočítáme při importu vždy, nebo až při přípravě audia.
