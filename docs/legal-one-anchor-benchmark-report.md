# One-Anchor Legal Benchmark Report

This report documents the one-anchor JRC-Acquis article benchmark generated from the
config-driven benchmark pipeline.

## Test Run

- Config: `config/benchmark_generation/legal_one_anchor.toml`
- Command: `uv run python scripts/generate_benchmark.py --config config/benchmark_generation/legal_one_anchor.toml`
- Dataset: `jrc_acquis`
- Section type: `article`
- Anchor ID: `en:jrc21987A0207_06`
- Directions: `20` ordered language directions
- Rows with terminology: `20` of `20`
- Refined terms across the article benchmark: `160`

## Flow

1. The TOML config selects the JRC article source snapshot and sets `anchor_limit = 1`.
2. The benchmark pipeline keeps one shared `anchor_id` and expands it across all ordered
   language directions for `de`, `en`, `es`, `fr`, and `pt`.
3. Each selected target/reference article text is passed through the legal terminology
   stack: legal LLM extraction, Stanza/UD, XLM-R/NOBI, spaCy, IATE, Wikidata, and UNTERM.
4. The LLM refiner selects the final `refined` terminology group, capped at eight terms
   per row.
5. The manifest stores both diagnostic candidate terms and final `refined` terms.

## Figure Legend

- Gray underline: extracted candidate term from LLM or deterministic extractors.
- Blue underline: LLM-refined final term.
- Green underline: refined term that also has verifier evidence.

## Article Text By Language

### German (`de`)

- Direction shown: `en-de`
- Candidate/verified terms: `56`
- Refined terms: `8`
- Verified refined terms: `7`
- Term groups: `algorithmic` = `33`, `llm` = `10`, `refined` = `8`, `verified` = `13`

![German article terminology underlines](figures/legal-one-anchor-benchmark/article-anchor-de-terms.png)

Selected refined terms:

- `Europäische Wirtschaftsgemeinschaft` (`iate`)
- `ZUSATZPROTOKOLL` (`iate`)
- `Inkrafttreten` (`iate`)
- `Europarat` (`iate`)
- `Unterzeichnung` (`iate`)
- `Notifikation` (`iate`)
- `Annahme` (`iate`)
- `EUROPÄISCHEN ÜBEREINKOMMEN`

### English (`en`)

- Direction shown: `de-en`
- Candidate/verified terms: `52`
- Refined terms: `8`
- Verified refined terms: `7`
- Term groups: `algorithmic` = `26`, `llm` = `9`, `refined` = `8`, `verified` = `17`

![English article terminology underlines](figures/legal-one-anchor-benchmark/article-anchor-en-terms.png)

Selected refined terms:

- `MEMBER STATES OF THE COUNCIL OF EUROPE` (`wikipedia`)
- `European Economic Community` (`iate, wikipedia`)
- `ADDITIONAL PROTOCOL` (`iate`)
- `Contracting Parties` (`iate`)
- `entry into force` (`iate`)
- `Agreement` (`iate`)
- `instrument of acceptance` (`iate`)
- `exempt from all import duties`

### Spanish (`es`)

- Direction shown: `en-es`
- Candidate/verified terms: `53`
- Refined terms: `8`
- Verified refined terms: `8`
- Term groups: `algorithmic` = `30`, `llm` = `5`, `refined` = `8`, `verified` = `18`

![Spanish article terminology underlines](figures/legal-one-anchor-benchmark/article-anchor-es-terms.png)

Selected refined terms:

- `Comunidad Económica Europea` (`iate, wikipedia`)
- `PROTOCOLO ADICIONAL` (`iate`)
- `Partes Contratantes` (`iate`)
- `entrada en vigor` (`iate`)
- `ACUERDO EUROPEO` (`iate`)
- `instrumento de aceptación` (`iate`)
- `derechos de importación` (`iate`)
- `Tratado constitutivo` (`iate`)

### French (`fr`)

- Direction shown: `en-fr`
- Candidate/verified terms: `49`
- Refined terms: `8`
- Verified refined terms: `7`
- Term groups: `algorithmic` = `30`, `llm` = `4`, `refined` = `8`, `verified` = `15`

![French article terminology underlines](figures/legal-one-anchor-benchmark/article-anchor-fr-terms.png)

Selected refined terms:

- `Communauté économique européenne` (`iate, wikipedia`)
- `PROTOCOLE ADDITIONNEL` (`iate`)
- `Conseil de l'Europe` (`iate`)
- `entrée en vigueur` (`iate`)
- `ACCORD EUROPÉEN` (`iate`)
- `instrument d'acceptation` (`iate`)
- `parties contractantes` (`iate`)
- `secrétaire général du Conseil de l'Europe`

### Portuguese (`pt`)

- Direction shown: `en-pt`
- Candidate/verified terms: `40`
- Refined terms: `8`
- Verified refined terms: `8`
- Term groups: `algorithmic` = `32`, `refined` = `8`, `verified` = `8`

![Portuguese article terminology underlines](figures/legal-one-anchor-benchmark/article-anchor-pt-terms.png)

Selected refined terms:

- `Comunidade Económica Europeia` (`iate`)
- `Conselho da Europa` (`iate`)
- `Secretário-geral` (`iate`)
- `Partes Contratantes` (`iate`)
- `Protocolo Adicional` (`iate`)
- `Parte Contratante` (`iate`)
- `Grupos Sanguíneos` (`iate`)
- `instrumento de aceitação` (`iate`)

