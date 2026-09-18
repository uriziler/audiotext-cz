# Book Translator

CLI nástroj, který přeloží knihu (`.txt` nebo `.epub`) přes OpenAI API. Výchozí
směr je z angličtiny do češtiny, ale jazyky lze nastavit libovolně.

Je to samostatný Python nástroj, nezávislý na Android aplikaci AudioText CZ v
tomto repozitáři.

## Jak to funguje

1. **Parsování** — `.txt` se rozdělí na odstavce (podle prázdných řádků);
   `.epub` se projde po jednotlivých HTML dokumentech a vytáhnou se textové
   bloky (`<p>`, `<li>`, nadpisy, `<blockquote>`, buňky tabulek atd.).
2. **Odesílání** — odstavce se seskupí do dávek (podle počtu znaků/odstavců) a
   pošlou se na Chat Completions API s instrukcí přeložit každý segment
   zvlášť a vrátit stejný počet segmentů jako JSON. Pokud odpověď neodpovídá
   počtu segmentů, dávka se rozpůlí a zkusí znovu (až na úroveň jednoho
   odstavce), takže jeden špatný výstup nezkazí celou dávku.
3. **Skládání** — přeložené odstavce se poskládají zpět: u `.txt` do nového
   textového souboru, u `.epub` zpátky do původních HTML uzlů a uloží se nové
   `.epub`.

Průběžné překlady se cachují do `<input>.cache.json` (klíčováno hash
odstavce + model + jazyky), takže přerušený běh (chyba API, spadlé
připojení, ...) lze bez placení navíc jednoduše spustit znovu — hotové
odstavce se přeskočí.

## Instalace

```bash
cd book-translator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # a doplň OPENAI_API_KEY
export OPENAI_API_KEY=sk-...
```

## Použití

```bash
# odhad rozsahu bez volání API
python3 translate_book.py kniha.txt --dry-run

# překlad txt knihy (výstup: kniha.cs.txt)
python3 translate_book.py kniha.txt

# překlad epub knihy do explicitního výstupu
python3 translate_book.py kniha.epub kniha_cz.epub

# jiný model / jiné jazyky / vyšší souběžnost
python3 translate_book.py kniha.txt --model gpt-4o --source-lang en --target-lang cs --concurrency 8
```

### Nejdůležitější přepínače

| Přepínač | Význam | Default |
| --- | --- | --- |
| `--source-lang` / `--target-lang` | jazykové kódy | `en` / `cs` |
| `--model` | OpenAI model pro překlad | `gpt-4o-mini` |
| `--max-chars` / `--max-paragraphs` | velikost dávky poslané v jednom requestu | `4000` / `40` |
| `--concurrency` | kolik dávek běží paralelně | `4` |
| `--no-cache` | vypne cache/resume | vypnuto |
| `--dry-run` | jen spočítá odstavce a znaky | vypnuto |

## Známá omezení (MVP)

- U `.epub` se vnitřní formátování odstavce (tučné/kurzíva/odkazy uvnitř
  jednoho `<p>`) při skládání nahradí prostým přeloženým textem — struktura
  kapitol/odstavců zůstává, ale inline markup uvnitř odstavce se ztratí.
- U `.epub` zůstávají popisky v navigaci/obsahu (TOC) v původním jazyce —
  ebooklib generuje `nav.xhtml` vždy znovu z `book.toc`, takže se text
  kapitol samotných přeloží, ale položky obsahu ne.
- Nepodporuje `.pdf` ani `.mobi` (na `.epub` je lze převést např. nástrojem
  Calibre/`ebook-convert`).
- Cena a rychlost závisí na zvoleném modelu a délce knihy — u dlouhé knihy
  vyzkoušej nejdřív `--dry-run` a menší `--max-chars`/model pro odhad nákladů.
