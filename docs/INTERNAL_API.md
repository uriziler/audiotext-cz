# Interní API design v0.1

## Cíl

AudioText CZ v MVP nemá backend ani HTTP API. Tento dokument proto definuje interní kontrakty mezi moduly Android aplikace:

- co smí volat UI
- co smí volat workery
- jak vypadají use cases
- jak repository oddělují domain vrstvu od Room/FileStorage
- jak se napojí fake a reálný transcription engine
- jak se mapují chyby

Dokument je most mezi architekturou, datovým modelem a první implementací.

## Základní pravidla

- UI volá use cases přes ViewModely.
- UI nevolá repository, Room DAO, FileStorage ani `TranscriptionEngine` přímo.
- Worker může volat use cases nebo orchestration služby určené pro background práci.
- Repository vrací doménové modely, ne Room entity.
- Platformní typy jako Android `Uri` nesmí protékat hluboko do domain vrstvy.
- Native/JNI chyby se mapují na doménový error model.
- Fake implementace musí dodržovat stejná rozhraní jako produkční implementace.

## Výsledek operací

Domain vrstva používá jednotný result typ:

```kotlin
sealed interface AppResult<out T> {
    data class Success<T>(val value: T) : AppResult<T>
    data class Failure(val error: AppError) : AppResult<Nothing>
}
```

Suspend funkce, které mohou selhat očekávaným způsobem, vrací `AppResult<T>`. Neočekávané výjimky se zachytí na hranici use case / worker a převedou na `AppError.Unexpected`.

## Error model

```kotlin
sealed interface AppError {
    val code: String
    val message: String
    val causeMessage: String?

    data class RecordingNotFound(
        override val code: String = "recording_not_found",
        override val message: String = "Nahrávka nebyla nalezena.",
        override val causeMessage: String? = null,
    ) : AppError

    data class ModelNotReady(
        val modelId: WhisperModelId,
        override val code: String = "model_not_ready",
        override val message: String = "Vybraný model není stažený.",
        override val causeMessage: String? = null,
    ) : AppError

    data class AudioImportFailed(
        override val code: String = "audio_import_failed",
        override val message: String = "Audio se nepodařilo importovat.",
        override val causeMessage: String? = null,
    ) : AppError

    data class AudioDecodeFailed(
        override val code: String = "audio_decode_failed",
        override val message: String = "Audio se nepodařilo připravit pro přepis.",
        override val causeMessage: String? = null,
    ) : AppError

    data class ModelDownloadFailed(
        val modelId: WhisperModelId,
        override val code: String = "model_download_failed",
        override val message: String = "Model se nepodařilo stáhnout.",
        override val causeMessage: String? = null,
    ) : AppError

    data class ModelChecksumMismatch(
        val modelId: WhisperModelId,
        override val code: String = "model_checksum_mismatch",
        override val message: String = "Stažený model neodpovídá očekávanému kontrolnímu součtu.",
        override val causeMessage: String? = null,
    ) : AppError

    data class TranscriptionFailed(
        override val code: String = "transcription_failed",
        override val message: String = "Přepis selhal.",
        override val causeMessage: String? = null,
    ) : AppError

    data class ExportFailed(
        override val code: String = "export_failed",
        override val message: String = "Export se nepodařil.",
        override val causeMessage: String? = null,
    ) : AppError

    data class Unexpected(
        override val code: String = "unexpected_error",
        override val message: String = "Nastala neočekávaná chyba.",
        override val causeMessage: String? = null,
    ) : AppError
}
```

Pravidla:

- `code` je stabilní a ukládá se do databáze.
- `message` je bezpečná zpráva pro UI.
- `causeMessage` je volitelná diagnostika, ne primární UI text.

## ID a value objects

```kotlin
@JvmInline value class RecordingId(val value: String)
@JvmInline value class TranscriptSegmentId(val value: String)
@JvmInline value class TranscriptionJobId(val value: String)

enum class WhisperModelId {
    BASE,
    SMALL,
    MEDIUM,
    LARGE,
}

@JvmInline value class LanguageCode(val value: String)
```

Výchozí hodnoty:

```kotlin
val DefaultLanguageCode = LanguageCode("cs")
val DefaultModelId = WhisperModelId.SMALL
```

## Use cases volané z UI

### ListRecordingsUseCase

```kotlin
class ListRecordingsUseCase(
    private val recordingRepository: RecordingRepository,
) {
    fun observe(): Flow<List<Recording>>
}
```

Použití:

- seznam nahrávek
- obnovování UI po změnách stavu

### GetRecordingDetailUseCase

```kotlin
class GetRecordingDetailUseCase(
    private val recordingRepository: RecordingRepository,
    private val transcriptSegmentRepository: TranscriptSegmentRepository,
) {
    fun observe(recordingId: RecordingId): Flow<RecordingDetail>
}
```

Vrací:

```kotlin
data class RecordingDetail(
    val recording: Recording,
    val segments: List<TranscriptSegment>,
    val latestJob: TranscriptionJob?,
)
```

### ImportRecordingUseCase

```kotlin
class ImportRecordingUseCase(
    private val audioImportGateway: AudioImportGateway,
    private val recordingRepository: RecordingRepository,
    private val settingsRepository: SettingsRepository,
) {
    suspend fun execute(request: ImportRecordingRequest): AppResult<Recording>
}
```

Vstup:

```kotlin
data class ImportRecordingRequest(
    val source: ImportAudioSource,
    val titleOverride: String? = null,
)
```

Platformní hranice:

```kotlin
sealed interface ImportAudioSource {
    data class PlatformUri(val value: String) : ImportAudioSource
}
```

Pravidla:

- Android `Uri` se převede na String na UI/platform hranici.
- Use case vytvoří `Recording` s `languageCode = "cs"` a `selectedModelId = SMALL`, pokud settings neurčí jinak.
- Originální soubor se kopíruje do interního app storage.

### StartTranscriptionUseCase

```kotlin
class StartTranscriptionUseCase(
    private val recordingRepository: RecordingRepository,
    private val modelRepository: ModelRepository,
    private val transcriptionJobScheduler: TranscriptionJobScheduler,
) {
    suspend fun execute(request: StartTranscriptionRequest): AppResult<TranscriptionJobId>
}
```

Vstup:

```kotlin
data class StartTranscriptionRequest(
    val recordingId: RecordingId,
    val modelId: WhisperModelId,
    val languageCode: LanguageCode = DefaultLanguageCode,
)
```

Pravidla:

- Pokud recording neexistuje, vrací `RecordingNotFound`.
- Pokud model není `ready`, nastaví recording na `waitingForModel` a vrací `ModelNotReady`.
- Pokud vše sedí, vytvoří job ve stavu `queued` a předá ho scheduleru.
- Nepouští `TranscriptionEngine` přímo; to dělá worker.

### UpdateTranscriptSegmentUseCase

```kotlin
class UpdateTranscriptSegmentUseCase(
    private val transcriptSegmentRepository: TranscriptSegmentRepository,
) {
    suspend fun execute(segmentId: TranscriptSegmentId, text: String): AppResult<Unit>
}
```

Pravidla:

- Trimuje okraje textu, ale nemaže záměrné vnitřní mezery.
- Nastaví `isEdited = true`.
- Aktualizuje `updatedAt`.

### ExportTranscriptUseCase

```kotlin
class ExportTranscriptUseCase(
    private val recordingRepository: RecordingRepository,
    private val transcriptSegmentRepository: TranscriptSegmentRepository,
    private val exportFormatter: ExportFormatter,
    private val exportGateway: ExportGateway,
) {
    suspend fun execute(request: ExportTranscriptRequest): AppResult<ExportFile>
}
```

Vstup:

```kotlin
data class ExportTranscriptRequest(
    val recordingId: RecordingId,
    val format: ExportFormat = ExportFormat.TXT,
)

enum class ExportFormat {
    TXT,
}
```

Pravidla:

- MVP podporuje pouze TXT.
- Export řadí segmenty podle `segmentIndex`.
- Export neukládá historii exportů do databáze.

## Use cases pro Model Management

### ListModelsUseCase

```kotlin
class ListModelsUseCase(
    private val modelCatalog: ModelCatalog,
    private val modelRepository: ModelRepository,
) {
    fun observe(): Flow<List<ModelListItem>>
}
```

Vrací:

```kotlin
data class ModelListItem(
    val definition: WhisperModelDefinition,
    val localModel: LocalModel,
)
```

### DownloadModelUseCase

```kotlin
class DownloadModelUseCase(
    private val modelRepository: ModelRepository,
    private val modelDownloadScheduler: ModelDownloadScheduler,
) {
    suspend fun execute(modelId: WhisperModelId): AppResult<Unit>
}
```

Pravidla:

- Pokud model už je `ready`, vrací success.
- Pokud model běží `downloading`, neplánuje duplicitu.
- Jinak nastaví stav na `downloading` a naplánuje worker.

### DeleteModelUseCase

```kotlin
class DeleteModelUseCase(
    private val modelRepository: ModelRepository,
    private val modelFileStorage: ModelFileStorage,
) {
    suspend fun execute(modelId: WhisperModelId): AppResult<Unit>
}
```

Pravidla:

- Smaže fyzický modelový soubor.
- Nastaví `localPath = null`.
- Nastaví `status = notDownloaded`.
- Nemaže žádné nahrávky ani přepisy vytvořené tímto modelem.

## Worker orchestration API

### TranscriptionJobScheduler

```kotlin
interface TranscriptionJobScheduler {
    suspend fun enqueue(jobId: TranscriptionJobId): AppResult<Unit>
}
```

Implementace:

- v produkci WorkManager
- v unit/integration testech fake scheduler

### ModelDownloadScheduler

```kotlin
interface ModelDownloadScheduler {
    suspend fun enqueue(modelId: WhisperModelId): AppResult<Unit>
}
```

### RunTranscriptionJobUseCase

Use case volaný workerem.

```kotlin
class RunTranscriptionJobUseCase(
    private val recordingRepository: RecordingRepository,
    private val transcriptionJobRepository: TranscriptionJobRepository,
    private val modelRepository: ModelRepository,
    private val audioPreprocessor: AudioPreprocessor,
    private val transcriptionEngine: TranscriptionEngine,
    private val transcriptSegmentRepository: TranscriptSegmentRepository,
    private val workingAudioCleaner: WorkingAudioCleaner,
) {
    suspend fun execute(jobId: TranscriptionJobId): AppResult<Unit>
}
```

Pravidla:

- Worker předává pouze `jobId`.
- Use case načte recording, job a model z repository.
- Při chybě aktualizuje job i recording.
- Segmenty ukládá průběžně, pokud engine podporuje streamované callbacky; jinak po dokončení.
- Po úspěchu nastaví recording na `completed`.

### RunModelDownloadUseCase

Use case volaný download workerem.

```kotlin
class RunModelDownloadUseCase(
    private val modelCatalog: ModelCatalog,
    private val modelRepository: ModelRepository,
    private val modelDownloader: ModelDownloader,
    private val checksumVerifier: ChecksumVerifier,
    private val modelFileStorage: ModelFileStorage,
) {
    suspend fun execute(modelId: WhisperModelId): AppResult<Unit>
}
```

Pravidla:

- Stahuje do dočasné cesty.
- Po úspěšném checksumu přesune soubor na finální cestu.
- Při selhání uklidí dočasný soubor, pokud to jde.

## Repository rozhraní

### RecordingRepository

```kotlin
interface RecordingRepository {
    fun observeAll(): Flow<List<Recording>>
    fun observeDetail(recordingId: RecordingId): Flow<Recording?>
    suspend fun get(recordingId: RecordingId): Recording?
    suspend fun create(newRecording: NewRecording): Recording
    suspend fun updateStatus(recordingId: RecordingId, status: RecordingStatus)
    suspend fun updateError(recordingId: RecordingId, error: AppError)
    suspend fun updateWorkingAudioPath(recordingId: RecordingId, path: String?)
    suspend fun markCompleted(recordingId: RecordingId, modelId: WhisperModelId)
    suspend fun delete(recordingId: RecordingId)
}
```

### TranscriptSegmentRepository

```kotlin
interface TranscriptSegmentRepository {
    fun observeForRecording(recordingId: RecordingId): Flow<List<TranscriptSegment>>
    suspend fun listForRecording(recordingId: RecordingId): List<TranscriptSegment>
    suspend fun replaceForRecording(
        recordingId: RecordingId,
        segments: List<TranscriptSegmentDraft>,
    )
    suspend fun appendForRecording(
        recordingId: RecordingId,
        segments: List<TranscriptSegmentDraft>,
    )
    suspend fun updateText(segmentId: TranscriptSegmentId, text: String)
    suspend fun deleteForRecording(recordingId: RecordingId)
}
```

### ModelRepository

```kotlin
interface ModelRepository {
    fun observeAll(): Flow<List<LocalModel>>
    suspend fun list(): List<LocalModel>
    suspend fun get(id: WhisperModelId): LocalModel?
    suspend fun ensureCatalogModels(definitions: List<WhisperModelDefinition>)
    suspend fun markDownloading(id: WhisperModelId)
    suspend fun updateDownloadProgress(id: WhisperModelId, downloadedBytes: Long, totalBytes: Long?)
    suspend fun markReady(id: WhisperModelId, localPath: String)
    suspend fun markFailed(id: WhisperModelId, error: AppError)
    suspend fun markNotDownloaded(id: WhisperModelId)
}
```

### TranscriptionJobRepository

```kotlin
interface TranscriptionJobRepository {
    fun observeLatestForRecording(recordingId: RecordingId): Flow<TranscriptionJob?>
    suspend fun createQueued(request: StartTranscriptionRequest): TranscriptionJob
    suspend fun get(jobId: TranscriptionJobId): TranscriptionJob?
    suspend fun markRunning(jobId: TranscriptionJobId)
    suspend fun updateProgress(jobId: TranscriptionJobId, progress: TranscriptionProgress)
    suspend fun markCompleted(jobId: TranscriptionJobId)
    suspend fun markFailed(jobId: TranscriptionJobId, error: AppError)
    suspend fun markCancelled(jobId: TranscriptionJobId)
}
```

### SettingsRepository

```kotlin
interface SettingsRepository {
    fun observe(): Flow<AppSettings>
    suspend fun get(): AppSettings
    suspend fun updateDefaultModel(modelId: WhisperModelId)
    suspend fun updateAllowMobileDataForModelDownload(allowed: Boolean)
}
```

## Platform gateway rozhraní

### AudioImportGateway

```kotlin
interface AudioImportGateway {
    suspend fun import(source: ImportAudioSource, titleOverride: String?): AppResult<ImportedAudio>
}
```

Vrací:

```kotlin
data class ImportedAudio(
    val title: String,
    val originalFileName: String?,
    val localPath: String,
    val mimeType: String?,
    val sizeBytes: Long?,
    val durationMs: Long?,
)
```

### AudioPreprocessor

```kotlin
interface AudioPreprocessor {
    suspend fun prepareForTranscription(recording: Recording): AppResult<PreparedAudio>
}
```

### ModelDownloader

```kotlin
interface ModelDownloader {
    suspend fun download(request: ModelDownloadRequest): AppResult<ModelDownloadResult>
}
```

### ChecksumVerifier

```kotlin
interface ChecksumVerifier {
    suspend fun verifySha256(path: String, expectedSha256: String): AppResult<Unit>
}
```

### ExportGateway

```kotlin
interface ExportGateway {
    suspend fun saveTextFile(fileName: String, content: String): AppResult<ExportFile>
}
```

### File storage

```kotlin
interface ModelFileStorage {
    suspend fun temporaryPathFor(modelId: WhisperModelId): String
    suspend fun finalPathFor(modelId: WhisperModelId, fileName: String): String
    suspend fun moveToFinalPath(tempPath: String, finalPath: String): AppResult<Unit>
    suspend fun deleteModel(path: String): AppResult<Unit>
}

interface RecordingFileStorage {
    suspend fun deleteRecordingFiles(recording: Recording): AppResult<Unit>
}

interface WorkingAudioCleaner {
    suspend fun clean(recording: Recording, preparedAudio: PreparedAudio?): AppResult<Unit>
}
```

## Transcription engine kontrakt

```kotlin
interface TranscriptionEngine {
    suspend fun transcribe(
        request: TranscriptionRequest,
        progress: suspend (TranscriptionProgress) -> Unit = {},
        onSegment: suspend (TranscriptSegmentDraft) -> Unit = {},
    ): AppResult<TranscriptionResult>
}
```

Vstup:

```kotlin
data class TranscriptionRequest(
    val recordingId: RecordingId,
    val audioPath: String,
    val modelPath: String,
    val modelId: WhisperModelId,
    val languageCode: LanguageCode,
    val translate: Boolean = false,
)
```

Progress:

```kotlin
data class TranscriptionProgress(
    val progressPercent: Int,
    val processedDurationMs: Long? = null,
    val totalDurationMs: Long? = null,
)
```

Výstup:

```kotlin
data class TranscriptionResult(
    val segments: List<TranscriptSegmentDraft>,
    val durationMs: Long?,
    val engineInfo: String?,
)
```

Pravidla:

- Fake i reálný engine musí implementovat stejné rozhraní.
- `languageCode` je v MVP vždy `cs`, pokud později nepřidáme výběr jazyka.
- `translate` je v MVP vždy `false`.
- Engine nesmí zapisovat přímo do Room.
- Engine nesmí měnit Recording status.
- Engine může posílat průběžné segmenty přes `onSegment`.
- Orchestration use case rozhoduje, kdy a jak se segmenty uloží.

### FakeTranscriptionEngine

Použití:

- první UI flow
- unit/integration testy
- vývoj bez NDK/whisper.cpp

Chování:

- vrací deterministické segmenty
- podporuje umělý progress
- umí simulovat chybu přes parametr nebo konfiguraci

Příklad segmentů:

```text
0-4000: Tohle je testovací přepis.
4000-9000: Druhý segment přepisu.
9000-13000: Přepis běží lokálně v telefonu.
```

### WhisperCppTranscriptionEngine

Použití:

- produkční lokální přepis

Pravidla:

- drží native/JNI kód mimo domain vrstvu
- načte vždy jen jeden model
- mapuje native chyby na `AppError.TranscriptionFailed`
- musí uvolnit native resources po dokončení nebo chybě

## Model catalog kontrakt

```kotlin
interface ModelCatalog {
    fun listSupportedModels(): List<WhisperModelDefinition>
    fun getDefinition(modelId: WhisperModelId): WhisperModelDefinition?
}
```

Definice:

```kotlin
data class WhisperModelDefinition(
    val id: WhisperModelId,
    val displayName: String,
    val qualityLabel: String,
    val fileName: String,
    val downloadUrl: String,
    val sha256: String,
    val approximateSizeMb: Int,
    val recommendedUse: String,
)
```

MVP modely:

```text
BASE
SMALL
MEDIUM
LARGE
```

Otevřená část:

- přesné `downloadUrl`
- přesné `sha256`
- potvrzení Large varianty po testu na S25 Ultra

## ViewModel kontrakty

ViewModely drží UI state a překládají uživatelské akce na use cases.

### RecordingsViewModel

Akce:

```kotlin
sealed interface RecordingsAction {
    data object ImportClicked : RecordingsAction
    data class ImportSelected(val source: ImportAudioSource) : RecordingsAction
    data class RecordingClicked(val recordingId: RecordingId) : RecordingsAction
    data class DeleteRecording(val recordingId: RecordingId) : RecordingsAction
}
```

State:

```kotlin
data class RecordingsUiState(
    val recordings: List<RecordingListItem>,
    val isImporting: Boolean,
    val errorMessage: String?,
)
```

### RecordingDetailViewModel

Akce:

```kotlin
sealed interface RecordingDetailAction {
    data class StartTranscription(val modelId: WhisperModelId) : RecordingDetailAction
    data class UpdateSegmentText(val segmentId: TranscriptSegmentId, val text: String) : RecordingDetailAction
    data object ExportTxt : RecordingDetailAction
}
```

State:

```kotlin
data class RecordingDetailUiState(
    val recording: Recording?,
    val segments: List<TranscriptSegment>,
    val latestJob: TranscriptionJob?,
    val availableModels: List<ModelListItem>,
    val isBusy: Boolean,
    val errorMessage: String?,
)
```

### ModelsViewModel

Akce:

```kotlin
sealed interface ModelsAction {
    data class Download(val modelId: WhisperModelId) : ModelsAction
    data class Delete(val modelId: WhisperModelId) : ModelsAction
}
```

State:

```kotlin
data class ModelsUiState(
    val models: List<ModelListItem>,
    val errorMessage: String?,
)
```

## Přístupová pravidla mezi moduly

Povolené:

- UI -> ViewModel
- ViewModel -> UseCase
- UseCase -> Repository interface
- UseCase -> Scheduler interface
- Worker -> Run*UseCase
- Repository implementation -> Room DAO
- Platform gateway implementation -> Android APIs
- `WhisperCppTranscriptionEngine` -> JNI/native bridge

Zakázané:

- UI -> Room DAO
- UI -> `TranscriptionEngine`
- UI -> FileStorage
- Repository -> Compose/UI
- Domain -> Android `Context`
- Domain -> Room entity
- `TranscriptionEngine` -> Room DAO

## Testovací kontrakty

Každé důležité rozhraní musí mít fake implementaci:

- `FakeRecordingRepository`
- `FakeTranscriptSegmentRepository`
- `FakeModelRepository`
- `FakeTranscriptionJobRepository`
- `FakeTranscriptionEngine`
- `FakeTranscriptionJobScheduler`
- `FakeModelDownloadScheduler`

Prioritní unit testy:

- `StartTranscriptionUseCase` vrací `ModelNotReady`, když model není stažený.
- `StartTranscriptionUseCase` vytvoří queued job, když model existuje.
- `RunTranscriptionJobUseCase` při úspěchu uloží segmenty a nastaví recording na `completed`.
- `RunTranscriptionJobUseCase` při chybě nastaví job i recording na failed.
- `ExportTranscriptUseCase` exportuje segmenty ve správném pořadí.
- `DownloadModelUseCase` neplánuje duplicitní download.

## Otevřená rozhodnutí

- Jestli AppSettings implementovat přes Room, nebo DataStore.
- Jestli download worker použije Android DownloadManager, nebo vlastní HTTP klient.
- Jestli transcription progress bude ukládat každý update, nebo throttlovat zápisy.
- Jestli `onSegment` ukládat průběžně, nebo až po dokončení pro MVP.
- Přesný formát UI state pro Compose obrazovky se doladí při implementaci.
