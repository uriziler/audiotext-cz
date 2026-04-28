# PROJECT_CONTEXT

## Název projektu

AudioText CZ

## Cíl projektu

Vytvořit Android aplikaci AudioText CZ pro Samsung S25 Ultra, do které uživatel nahraje audio nahrávku a aplikace ji lokálně přepíše do textu pomocí Whisper modelu. Výchozí jazyk přepisu je čeština. MVP je offline a bez cloudu.

## Cíloví uživatelé

- Jeden hlavní uživatel: člověk, který chce na telefonu převádět vlastní nahrávky do českého textu.
- Technicky středně zdatný uživatel: zvládne vybrat soubor, stáhnout model a počkat na zpracování.

## Domény

- Recording: správa nahrávek a jejich metadat.
- Model Management: stažení, ověření, výběr a mazání lokálních Whisper modelů.
- Transcription: lokální přepis audia do segmentovaného textu.
- Audio Processing: import, dekódování a převod audia do formátu vhodného pro Whisper.
- Transcript Editing and Export: zobrazení, úprava a export výsledku.

## Hlavní entity

- Recording
- TranscriptSegment
- WhisperModel
- TranscriptionJob
- ExportFile

## Zdroj pravdy

- Recording doména vlastní metadata nahrávky a stav přepisu.
- Transcription doména vlastní výsledné segmenty přepisu.
- Model Management doména vlastní dostupnost modelů, jejich soubory, checksums a výběr aktivního modelu.
- Audio Processing doména vlastní lokální audio soubory a odvozené pracovní audio formáty.

## Typ architektury

- Modulární monolit v jedné Android aplikaci.
- Local-first/offline-first.
- Bez backendu v MVP.
- Bez cloud transcription v MVP.

## Technologické rozhodnutí pro MVP

- Platforma: Android.
- Jazyk: Kotlin.
- UI: Jetpack Compose.
- Lokální inference: whisper.cpp přes JNI/NDK.
- Dlouhé úlohy: WorkManager nebo foreground worker.
- Lokální data: Room.
- Souborové úložiště: interní app storage.
- Import audia: Android Storage Access Framework.
- Audio decode/preprocessing: Android MediaExtractor/MediaCodec, pokud bude stačit pro podporované formáty.

## Modely v MVP

Appka má podporovat tyto lokální modelové volby:

- Base: lehčí model pod Small pro rychlé testy a úspornější přepis.
- Small: defaultní model pro rychlý běžný přepis.
- Medium: přesnější model s většími nároky.
- Large: nejlepší dostupný lokální režim pro kvalitu, ne default.

Interně preferovat quantized multilingual whisper.cpp modely. Všechny modely musí podporovat češtinu. Nepoužívat `.en` varianty.

Výchozí nastavení:

- language: `cs`
- task: `transcribe`
- translate: `false`
- default model: `small`

## Moduly

### Modul: Recording

- Odpovědnost: Evidence nahrávek, stavů a vazeb na přepisy.
- Vstupy: Importovaný audio soubor, uživatelské akce v seznamu/detailu.
- Výstupy: Recording metadata, stav nahrávky, vazba na transkripci.
- Závislosti: Storage, Room, Transcription.

### Modul: Model Management

- Odpovědnost: Správa lokálních Whisper modelů.
- Vstupy: Volba modelu, požadavek na stažení/smazání.
- Výstupy: Dostupný modelový soubor, stav stažení, aktivní model.
- Závislosti: File storage, download client, checksum verifier.

### Modul: Audio Processing

- Odpovědnost: Převod importovaného audia do formátu vhodného pro Whisper.
- Vstupy: URI nebo lokální path nahrávky.
- Výstupy: PCM/working audio data v očekávaném formátu.
- Závislosti: Android media APIs.

### Modul: Transcription

- Odpovědnost: Lokální přepis audia pomocí vybraného Whisper modelu.
- Vstupy: Audio path, language, model id.
- Výstupy: Transcript segments se start/end časem a textem.
- Závislosti: whisper.cpp JNI wrapper, Model Management, Recording.

### Modul: Transcript Editing and Export

- Odpovědnost: Zobrazení, úprava a export přepisu.
- Vstupy: Segmenty přepisu, uživatelské úpravy.
- Výstupy: Uložené segmenty, TXT export, později SRT/VTT.
- Závislosti: Room, Android share/export APIs.

## Datový model

Detailní datový model je v [DATA_MODEL.md](DATA_MODEL.md). Shrnutí hlavních entit:

### Recording

- id
- title
- originalAudioPath
- workingAudioPath
- durationMs
- languageCode
- selectedModelId
- status
- createdAt
- updatedAt
- errorMessage

### TranscriptSegment

- id
- recordingId
- startMs
- endMs
- text
- segmentIndex
- updatedAt

### WhisperModel

- id
- displayName
- fileName
- downloadUrl
- sha256
- approximateSizeMb
- localPath
- status

### TranscriptionJob

- id
- recordingId
- modelId
- status
- progressPercent
- startedAt
- finishedAt
- errorMessage

## Vztahy

- Recording má 0..n TranscriptSegment.
- Recording má 0..1 aktivní TranscriptionJob.
- TranscriptionJob používá právě jeden WhisperModel.
- Recording si pamatuje model, kterým byl přepis vytvořen.

## Stavy

### RecordingStatus

- imported
- preparingAudio
- waitingForModel
- transcribing
- completed
- failed

### ModelStatus

- notDownloaded
- downloading
- ready
- failed

### TranscriptionJobStatus

- queued
- running
- completed
- failed
- cancelled

## Tok dat

1. Uživatel vybere audio soubor.
2. Aplikace vytvoří Recording a zkopíruje soubor do interního storage.
3. Aplikace zkontroluje, jestli je vybraný model stažený.
4. Pokud model chybí, uživatel ho stáhne přes Model Management.
5. Audio Processing připraví audio pro Whisper.
6. Transcription worker spustí whisper.cpp s `language = cs`.
7. Segmenty se průběžně ukládají do Room.
8. UI zobrazí přepis po segmentech.
9. Uživatel může text upravit a exportovat.

## API / interní rozhraní

MVP nemá HTTP API. Detailní interní API design je v [INTERNAL_API.md](INTERNAL_API.md). Shrnutí základních rozhraní:

### TranscriptionEngine

```kotlin
interface TranscriptionEngine {
    suspend fun transcribe(request: TranscriptionRequest): TranscriptionResult
}
```

### ModelRepository

```kotlin
interface ModelRepository {
    suspend fun listModels(): List<WhisperModel>
    suspend fun getModel(id: WhisperModelId): WhisperModel
    suspend fun markModelReady(id: WhisperModelId, localPath: String)
}
```

### RecordingRepository

```kotlin
interface RecordingRepository {
    suspend fun createFromImport(request: ImportRecordingRequest): Recording
    suspend fun updateStatus(recordingId: RecordingId, status: RecordingStatus)
    suspend fun saveSegments(recordingId: RecordingId, segments: List<TranscriptSegment>)
}
```

## Implementační pravidla

- UI používá ViewModely a neobsahuje transkripční logiku.
- Transcription logika nesmí být ve Composable funkcích.
- Přístup k Room jde přes repository.
- whisper.cpp je za rozhraním `TranscriptionEngine`.
- Model download a checksum ověření jsou oddělené od přepisu.
- Worker ukládá průběžný stav, aby se dala chyba zobrazit a diagnostikovat.
- Čeština je default, ale interně se drží jako `languageCode = "cs"`.
- V paměti je načtený vždy jen jeden Whisper model.

## Rozsah MVP

- Import audio souboru.
- Lokální evidence nahrávek.
- Stažení a výběr modelu Base / Small / Medium / Large.
- Lokální přepis přes whisper.cpp.
- Čeština jako defaultní jazyk.
- Zobrazení segmentovaného přepisu.
- Editace textu segmentů.
- Export do TXT.

## Mimo scope pro MVP

- Cloud transcription.
- Login a uživatelské účty.
- Synchronizace mezi zařízeními.
- Realtime přepis při nahrávání.
- Diarizace mluvčích.
- Shrnutí přepisu.
- Překlad do jiných jazyků.
- SRT/VTT export, pokud se nevejde do prvního řezu.

## Akceptační kritéria MVP

- Uživatel vybere audio soubor a aplikace ho uloží jako Recording.
- Uživatel vidí, které modely jsou dostupné a které je potřeba stáhnout.
- Uživatel může spustit přepis s modelem Base, Small, Medium nebo Large.
- Přepis používá češtinu jako výchozí jazyk.
- Přepis doběhne na testovací nahrávce a uloží segmenty do lokální databáze.
- Uživatel vidí text přepisu v detailu nahrávky.
- Uživatel může upravit text segmentu.
- Uživatel může exportovat přepis jako TXT.
- Aplikace zvládne chybu modelu nebo audia bez pádu.

## Testovací strategie

### Unit testy

- mapování stavů Recording/Job
- výběr modelu
- validace dostupnosti modelu
- export TXT
- převod segmentů do zobrazitelného textu

### Integrační testy

- RecordingRepository + Room
- ModelRepository + lokální metadata
- Transcription job state flow bez reálného Whisper modelu, přes fake engine

### Manuální testy na zařízení

- import krátké české nahrávky
- import delší české nahrávky
- přepis modelem Base
- přepis modelem Small
- přepis modelem Medium
- přepis modelem Large
- přerušení aplikace během přepisu
- nedostatek modelu před přepisem
- export TXT

## Refactoring pravidla

- Refaktorovat po dokončení každého modulu.
- Neměnit externí chování bez záměru.
- Větší změny chránit testy nebo fake implementací.
- Jakmile se objeví duplicitní stavové mapování, sjednotit ho.
- Jakmile začne UI rozhodovat o business pravidlech, přesunout rozhodnutí do use case vrstvy.

## Otevřená rozhodnutí

- Minimální podporovaná verze Androidu.
- Přesné modelové soubory a jejich download URL/checksum.
- Jestli package name `cz.local.audiotextcz` zůstane finální.
- Jestli Large v MVP zůstane `large-v3-turbo-q5_0` po měření na S25 Ultra.
- Jestli model download poběží přes Android DownloadManager, nebo vlastní HTTP klient.
- Jestli se `whisper.cpp` integruje jako vendored source, git submodule, nebo samostatný build artifact.
