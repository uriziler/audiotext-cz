# Architektura systému v0.1

## Typ architektury

AudioText CZ je modulární monolit v jedné Android aplikaci.

Architektura je local-first:

- bez backendu v MVP
- bez cloudového přepisu v MVP
- jedna Android codebase
- jedna lokální databáze
- jasné moduly podle domény
- `whisper.cpp` schovaný za interním rozhraním

## Hlavní části systému

- Android UI vrstva: Jetpack Compose obrazovky a navigace.
- Presentation state vrstva: ViewModely a UI state.
- Domain vrstva: use cases, entity a rozhraní modulů.
- Data vrstva: Room, repository implementace a file storage.
- Worker vrstva: dlouho běžící import, download a transcription úlohy.
- Native inference vrstva: JNI wrapper nad `whisper.cpp`.
- Platform vrstva: Android Storage Access Framework, media decoding, notifications, share/export.

## Moduly

### Modul: Recording

- Odpovědnost: Evidence nahrávek, stavů, názvů, audio cest a vazeb na přepis.
- Vstupy: Importovaný soubor, uživatelská akce smazání nebo otevření detailu.
- Výstupy: Recording entity, Recording UI state, vazby na segmenty.
- Závislosti: Room, FileStorage, Transcription.

### Modul: Model Management

- Odpovědnost: Katalog modelů, stažení, ověření checksumu, lokální dostupnost a mazání modelů.
- Vstupy: Model id, požadavek na stažení nebo smazání, síťový stav.
- Výstupy: Lokální cesta k modelu, ModelStatus, chyba stažení.
- Závislosti: DownloadManager nebo HTTP client, FileStorage, checksum verifier.

### Modul: Audio Processing

- Odpovědnost: Převod importovaného audio souboru do working formátu vhodného pro Whisper.
- Vstupy: Lokální cesta k originálnímu audio souboru.
- Výstupy: Working audio path nebo stream PCM dat.
- Závislosti: Android `MediaExtractor`, `MediaCodec`, případně později FFmpeg fallback.

### Modul: Transcription

- Odpovědnost: Řízení lokálního přepisu, výběr modelu, volání engine, ukládání segmentů a stavů.
- Vstupy: Recording id, model id, language code.
- Výstupy: TranscriptSegment entity, TranscriptionJob stav, chyba.
- Závislosti: `TranscriptionEngine`, RecordingRepository, SegmentRepository, ModelRepository.

### Modul: Transcript Editing and Export

- Odpovědnost: Editace segmentů a export výsledného textu.
- Vstupy: Segmenty, uživatelské úpravy, export akce.
- Výstupy: Upravené segmenty, TXT soubor, Android share intent.
- Závislosti: SegmentRepository, ExportFormatter, Android storage/share APIs.

### Modul: App Settings

- Odpovědnost: Výchozí model, výchozí jazyk, preference stahování přes mobilní data.
- Vstupy: Uživatelské nastavení.
- Výstupy: AppSettings hodnoty pro ostatní moduly.
- Závislosti: DataStore nebo jednoduché lokální preferences.

## Vrstvy

### Presentation

Obsahuje:

- Compose screens
- ViewModely
- UI state
- navigaci

Pravidla:

- nevolá `whisper.cpp` přímo
- nepracuje přímo s Room DAO
- nespouští dlouhé operace mimo use case / worker
- pouze zobrazuje stav a posílá uživatelské akce dál

### Domain

Obsahuje:

- entity a value objects
- use cases
- rozhraní repository a engines
- stavové enumy

Pravidla:

- neobsahuje Android UI závislosti
- definuje hranice mezi moduly
- drží business rozhodnutí, například jestli lze spustit přepis bez modelu

### Data

Obsahuje:

- Room entity a DAO
- repository implementace
- file storage implementace
- model catalog storage

Pravidla:

- neobsahuje UI logiku
- nepočítá transcription pravidla mimo jasně dané mapování dat
- ukládá stav tak, aby se appka dala obnovit po restartu

### Platform / Native

Obsahuje:

- Android media APIs
- WorkManager
- Notifications
- Storage Access Framework
- JNI bridge
- `whisper.cpp` native knihovnu

Pravidla:

- platformní detaily jsou schované za rozhraními
- domain vrstva nezná JNI ani Android media typy
- native chyby se mapují na doménové error typy

## Tok dat: Import nahrávky

1. Uživatel klepne na import.
2. UI otevře Android Storage Access Framework picker.
3. Uživatel vybere audio soubor.
4. `ImportRecordingUseCase` vytvoří Recording ve stavu `imported`.
5. FileStorage zkopíruje originální audio do interního app storage.
6. RecordingRepository uloží metadata a lokální cestu.
7. UI přejde na detail nebo zpět na seznam.

## Tok dat: Stažení modelu

1. Uživatel otevře Model Manager.
2. UI zobrazí katalog modelů Base, Small, Medium a Large.
3. Uživatel vybere model ke stažení.
4. `DownloadModelUseCase` ověří, jestli už model není lokálně dostupný.
5. Worker stáhne model do dočasného souboru.
6. Checksum verifier ověří soubor.
7. ModelRepository označí model jako `ready`.
8. Dočasný soubor se přesune na finální lokální cestu.

## Tok dat: Přepis

1. Uživatel spustí přepis nad Recording.
2. `StartTranscriptionUseCase` ověří existenci nahrávky a dostupnost modelu.
3. Recording přejde do stavu `preparingAudio`.
4. Audio Processing připraví working audio.
5. Recording přejde do stavu `transcribing`.
6. TranscriptionWorker zavolá `TranscriptionEngine`.
7. `WhisperCppTranscriptionEngine` přes JNI načte vybraný model.
8. Engine přepíše audio s `languageCode = "cs"` a `task = transcribe`.
9. Segmenty se průběžně ukládají přes SegmentRepository.
10. Po úspěchu Recording přejde do stavu `completed`.
11. Pracovní audio se smaže podle storage pravidla.
12. UI zobrazí hotový přepis.

## Tok dat: Editace a export

1. Uživatel otevře detail přepisu.
2. UI načte segmenty přes ViewModel.
3. Uživatel upraví text segmentu.
4. `UpdateTranscriptSegmentUseCase` uloží změnu.
5. Uživatel zvolí export TXT.
6. `ExportTranscriptUseCase` načte segmenty v pořadí.
7. `TxtExportFormatter` vytvoří textový výstup.
8. Platform export vrstva nabídne soubor přes Android share/save mechanismus.

## Role a oprávnění

MVP nemá uživatelské účty ani role.

Android oprávnění a přístupy:

- přístup k vybranému souboru přes Storage Access Framework
- internet pouze pro stažení modelů
- foreground service / notification pro dlouhé přepisy a downloady
- čtení běžného úložiště se nevyžaduje plošně, pokud stačí SAF

## Externí integrace

- Hugging Face nebo jiný model hosting: stažení modelových souborů.
- `whisper.cpp`: lokální inference engine.
- Android platform APIs: SAF, media decode, WorkManager, notifications, sharing.

Rizika:

- model hosting může být nedostupný
- model URL/checksum se může změnit
- `whisper.cpp` Android build může vyžadovat úpravy při updatech
- Android background execution limity mohou ovlivnit dlouhé úlohy

## Interní rozhraní

### TranscriptionEngine

```kotlin
interface TranscriptionEngine {
    suspend fun transcribe(request: TranscriptionRequest): TranscriptionResult
}
```

### ModelCatalog

```kotlin
interface ModelCatalog {
    fun listSupportedModels(): List<WhisperModelDefinition>
    fun getDefinition(modelId: WhisperModelId): WhisperModelDefinition
}
```

### ModelRepository

```kotlin
interface ModelRepository {
    suspend fun listModels(): List<WhisperModel>
    suspend fun getModel(id: WhisperModelId): WhisperModel
    suspend fun markDownloading(id: WhisperModelId)
    suspend fun markReady(id: WhisperModelId, localPath: String)
    suspend fun markFailed(id: WhisperModelId, reason: String)
}
```

### RecordingRepository

```kotlin
interface RecordingRepository {
    suspend fun create(recording: NewRecording): Recording
    suspend fun get(recordingId: RecordingId): Recording?
    suspend fun list(): List<Recording>
    suspend fun updateStatus(recordingId: RecordingId, status: RecordingStatus)
}
```

### TranscriptSegmentRepository

```kotlin
interface TranscriptSegmentRepository {
    suspend fun listForRecording(recordingId: RecordingId): List<TranscriptSegment>
    suspend fun replaceForRecording(recordingId: RecordingId, segments: List<TranscriptSegment>)
    suspend fun updateText(segmentId: TranscriptSegmentId, text: String)
}
```

### AudioPreprocessor

```kotlin
interface AudioPreprocessor {
    suspend fun prepareForTranscription(recording: Recording): PreparedAudio
}
```

### ExportFormatter

```kotlin
interface ExportFormatter {
    fun format(recording: Recording, segments: List<TranscriptSegment>): String
}
```

## Package struktura

Pracovní návrh:

```text
cz.local.audiotextcz
  app
  core
    data
    domain
    platform
    ui
  feature
    recordings
    models
    transcription
    transcript
    settings
  nativebridge
```

Alternativně lze jít ještě doménověji:

```text
cz.local.audiotextcz
  recording
    data
    domain
    ui
  models
    data
    domain
    ui
  transcription
    data
    domain
    worker
  audio
    platform
  export
    domain
    platform
```

Pro MVP preferujeme první variantu, protože je čitelnější při rychlém startu a dobře sedí na Compose aplikaci.

## Architektonická pravidla

- UI neobsahuje transcription logiku.
- UI nepracuje přímo s Room DAO.
- `whisper.cpp` je dostupný pouze přes `TranscriptionEngine`.
- Model download je oddělený od samotného přepisu.
- Audio preprocessing je oddělený od přepisu.
- Worker ukládá průběžný stav do databáze.
- Každá dlouhá operace má chybový stav viditelný v UI.
- Repository vrací doménové modely, ne Room entity.
- Native chyby se mapují na doménový error model.
- V paměti je načtený vždy jen jeden model.
- Přepis se spouští pouze s modelem ve stavu `ready`.

## První implementační řez

1. Založit Android projekt a package `cz.local.audiotextcz`.
2. Přidat základní Compose navigaci.
3. Přidat Room schema v1.
4. Přidat doménové entity a repository rozhraní.
5. Přidat fake `TranscriptionEngine`.
6. Implementovat import audio souboru a seznam nahrávek.
7. Implementovat detail nahrávky s fake segmenty.
8. Implementovat Model Manager bez reálného downloadu.
9. Přidat TXT export.
10. Teprve potom udělat technický spike `whisper.cpp` JNI/NDK.

## Otevřená rozhodnutí

- Minimální Android verze.
- Přesné modelové URL a checksumy.
- Jestli model download poběží přes Android DownloadManager nebo vlastní HTTP klient.
- Jestli `whisper.cpp` bude vendored source, git submodule, nebo separátní build artifact.
- Jestli se `large-v3-turbo-q5_0` potvrdí jako MVP Large po měření na S25 Ultra.
- Jestli bude audio preprocessing čistě přes Android media APIs, nebo přidáme FFmpeg fallback.
- Přesný error model pro native failures.
