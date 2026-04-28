# Start checklist

Tento checklist říká, co potřebujeme mít rozhodnuté nebo připravené, než začneme psát první produkční kód Android aplikace.

## 1. Produktové minimum

- Název aplikace: AudioText CZ.
- Potvrzené MVP: import audia, lokální modely Base/Small/Medium/Large, čeština jako default, lokální přepis, zobrazení textu, editace, TXT export.
- Potvrzené mimo scope: cloud, login, sync, diarizace, real-time přepis, AI shrnutí.
- Testovací audio nahrávky v češtině: krátká, střední, delší, čistá, horší kvalita.

## 2. Android rozhodnutí

- Package name, pracovní návrh: `cz.local.audiotextcz`.
- Minimální Android verze.
- Cílové zařízení pro ladění: Samsung S25 Ultra.
- Způsob založení projektu: čistý Android Studio / Gradle Kotlin project.
- UI framework: Jetpack Compose.

## 3. Lokální Whisper rozhodnutí

- Potvrdit integraci přes `whisper.cpp`.
- Rozhodnout, jestli `whisper.cpp` bude vendored source, git submodule, nebo samostatný build artifact.
- Připravit JNI/NDK/CMake build.
- Potvrdit modelové varianty:
  - Base: quantized multilingual model.
  - Small: quantized multilingual model.
  - Medium: quantized multilingual model.
  - Large: rozhodnout mezi `large-v3-turbo-q5_0` a plným `large-v3-q5_0`.
- Připravit download URL a checksums pro každý model.
- Určit, jestli se modely stahují pouze přes Wi-Fi, nebo i přes mobilní data po potvrzení.

## 4. Storage a data

- Rozhodnout, jestli se originální audio ponechává po přepisu.
- Rozhodnout, jestli se pracovní audio soubor po přepisu maže.
- Potvrdit Room jako lokální databázi.
- Potvrdit interní app storage pro modely a audio.
- Navrhnout migrace od začátku, i když první verze bude mít jen schema v1.

## 5. UX minimum

- Seznam nahrávek.
- Import obrazovka.
- Model manager obrazovka nebo dialog.
- Detail přepisu.
- Export akce.
- Stavové obrazovky pro chybějící model, probíhající přepis a chybu přepisu.

## 6. Vývojové prostředí

- Android Studio.
- JDK kompatibilní s aktuálním Android Gradle Pluginem.
- Android SDK.
- Android NDK.
- CMake.
- Připojený Samsung S25 Ultra s developer mode a USB debugging.
- Git repozitář.

## 7. První implementační řez

1. Založit Android projekt.
2. Přidat základní moduly/balíčky podle `PROJECT_CONTEXT.md`.
3. Přidat Room entity pro Recording, TranscriptSegment, WhisperModel a TranscriptionJob.
4. Přidat fake `TranscriptionEngine`, aby UI a workflow šly vyvíjet bez hotového whisper.cpp.
5. Postavit import audia a seznam nahrávek.
6. Postavit detail přepisu s fake segmenty.
7. Teprve potom napojit reálný whisper.cpp engine.

## 8. Hlavní otevřené otázky

- Potvrdíme package name `cz.local.audiotextcz`, nebo zvolíme jiný?
- Jakou minimální Android verzi chceme podporovat?
- Bude MVP umět vlastní nahrávání audia, nebo jen import souboru?
- Má být Large v MVP `large-v3-turbo-q5_0`, nebo plný `large-v3-q5_0`?
- Chceme TXT export jako jediný export v MVP, nebo rovnou i SRT?
- Inicializujeme tady rovnou Git repozitář?
