# Five-Language Candidate Extraction Comparison

This report compares two non-LLM candidate extraction methods on five anchored JRC-Acquis article
samples. Each sample uses a different target language: English, German, French, Spanish, and
Portuguese.

The two methods tested were:

- `stanza_ud`: deterministic Stanza/Universal Dependencies extraction with boundary cleanup.
- `xlmr_nobi`: XLM-R token classification with the NOBI-style term extraction checkpoint
  `tthhanh/xlm-ate-nobi-en-nes`.

The purpose of this run was candidate quality comparison, not final verified terminology selection.

## Integration Status

Two methods are currently integrated as terminology extractors:

- `TargetTerminologyExtractor`: Stanza/UD extractor.
- `XLMRNOBITerminologyExtractor`: XLM-R/NOBI extractor.

`DatasetTerminologyGenerator` can now run multiple extractors and union their outputs before
deduplication and optional verifier checks.

## Samples

The samples came from:

```text
benchmark_sources/jrc_acquis_anchored_articles_250_per_language_pair.jsonl
```

Selected rows:

- English: `es-en:jrc21987A0207_06:chunk-0182`
- German: `en-de:jrc21987A0207_06:chunk-0135`
- French: `en-fr:jrc21987A0207_06:chunk-0188`
- Spanish: `en-es:jrc21987A0207_06:chunk-0182`
- Portuguese: `en-pt:jrc21987A0207_06:chunk-0168`

## English Sample

Target text excerpt:

```text
ADDITIONAL PROTOCOL TO THE EUROPEAN AGREEMENT on the Exchanges of Blood-grouping Reagents THE MEMBER STATES OF THE COUNCIL OF EUROPE, Contracting Parties to the European Agreement of 14 May 1962 on the exchanges of blood-grouping reagents (hereinafter called "the Agreement"); Having regard to the provisions of Article 5, paragraph 1, of the Agreement, according to which 'The Contracting Parties shall take all necessary measures to exempt from all import duties the blood-grouping reagents placed at their disposal by the other Parties'; Consideri
```

### Stanza/UD

```text
European Economic Community
Contracting Parties
Contracting Party
MEMBER STATES
following such signature
blood-grouping reagents
Additional Protocol
necessary measures
following the date
Blood-grouping
```

### XLM-R/NOBI

```text
Council of Europe
European Economic Community
blood-grouping reagents
Protocol
import
```

## German Sample

Target text excerpt:

```text
ZUSATZPROTOKOLL ZU DEM EUROPÄISCHEN ÜBEREINKOMMEN über den Austausch von Reagenzien zur Blutgruppenbestimmung DIE MITGLIEDSTAATEN DES EUROPARATS, die Vertragsparteien des Europäischen Übereinkommens vom 14. Mai 1962 über den Austausch von Reagenzien zur Blutgruppenbestimmung sind (im folgenden als "Übereinkommen" bezeichnet) - gestützt auf Artikel 5 Absatz 1 des Übereinkommens, wonach "die Vertragsparteien alle notwendigen Maßnahmen" treffen, "um die ihnen von den anderen Parteien zur Verfügung gestellten therapeutischen Substanzen menschlichen
```

### Stanza/UD

```text
Europäischen Wirtschaftsgemeinschaft
Europäische Wirtschaftsgemeinschaft
Vertragspartei des Übereinkommens
Europäischen Übereinkommens
Europäische Wirtschaftsgemeinschaft Vertragspartei
MITGLIEDSTAATEN DES EUROPARATS
letzte der Vertragsparteien
erforderlichen Befugnisse
menschlichen Ursprungs
notwendigen Maßnahmen
```

### XLM-R/NOBI

```text
Europarats
Europäische Wirtschaftsgemeinschaft
Europäischen Wirtschaftsgemeinschaft
```

## French Sample

Target text excerpt:

```text
PROTOCOLE ADDITIONNEL À L'ACCORD EUROPÉEN relatif à l'échange des réactifs pour la détermination des groupes sanguins LES ÉTATS MEMBRES DU CONSEIL DE L'EUROPE, parties contractantes à l'accord européen, du 14 mai 1962, relatif à l'échange des réactifs pour la détermination des groupes sanguins (ci-après dénommé «l'accord»), vu les dispositions de l'article 5 paragraphe 1 de l'accord aux termes duquel «les parties contractantes prendront toutes mesures nécessaires en vue d'exempter de tous droits d'importation les réactifs pour la détermination
```

### Stanza/UD

```text
Communauté économique européenne
présent protocole additionnel
instrument d'acceptation
parties contractantes
protocole additionnel
pouvoirs nécessaires
mesures nécessaires
partie contractante
réactifs pour la détermination des groupes
premier jour du mois
```

### XLM-R/NOBI

```text
Communauté économique européenne
CONSEIL DE L'EUROPE
droits d
général
```

## Spanish Sample

Target text excerpt:

```text
PROTOCOLO ADICIONAL AL ACUERDO EUROPEO SOBRE INTERCAMBIO de Reactivos para la Determinación de los grupos sanguíneos LOS ESTADOS MIEMBROS DEL CONSEJO DE EUROPA, Partes Contratantes en el Acuerdo Europeo de 14 de mayo de 1962, relativo al intercambio de Reactivos para la Determinación de los Grupos Sanguíneos denominado en lo sucesivo «el Acuerdo», Vistas las disposiciones del apartado 1 del artículo 5 del Acuerdo, que establecen que «las Partes Contratantes adoptarán cuantas medidas fueren necesarias a fin de eximir de cualesquiera derechos de
```

### Stanza/UD

```text
Presente Protocolo Adicional
Comunidad Económica Europea
respecto de la Comunidad
Partes Contratantes
Protocolo Adicional
Secretario General
Grupos Sanguíneos
Parte Contratante
ESTADOS MIEMBROS
Acuerdo Europeo
```

### XLM-R/NOBI

```text
CONSEJO DE EUROPA
Comunidad Económica Europea
General
```

## Portuguese Sample

Target text excerpt:

```text
PROTOCOLO ADICIONAL AO ACORDO EUROPEU relativo ao intercâmbio de reagentes para determinação de grupos sanguíneos OS ESTADOS-MEMBROS DO CONSELHO DA EUROPA, Partes Contratantes no Acordo Europeu relativo ao Intercâmbio de Reagentes para Determinação de Grupos Sanguíneos, de 14 de Maio de 1962, a seguir denominado «Acordo», Tendo em conta o disposto no nº 1 do artigo 5° do Acordo, nos termos do qual «As Partes Contratantes tomarão todas as medidas necessárias para isentar de todos os direitos de importação os reagentes para determinação de grupos
```

### Stanza/UD

```text
Comunidade Económica Europeia
presente Protocolo Adicional
Partes Contratantes
Protocolo Adicional
Parte Contratante
Grupos Sanguíneos
Acordo Europeu
instrumento de aceitação
medidas necessárias
uma das Partes Contratantes
```

### XLM-R/NOBI

```text
Comunidade Económica Europeia
Conselho da Europa
Secretário-geral
Europeu
```

## Evaluation

### Stanza/UD

Stanza/UD has the best recall of the currently kept methods. It consistently finds plausible legal and
institutional phrases across all five languages. It also works without model-specific training and
does not need an LLM.

After adding boundary cleanup, the worst punctuation/list/citation issues are reduced. However,
some candidates remain too generic, such as `following such signature`, `necessary measures`, or
`premier jour du mois`. These are likely to remain unverified and should be treated as low-confidence
fallback candidates.

Use Stanza/UD as the broad deterministic candidate generator.

### XLM-R/NOBI

XLM-R/NOBI produces much cleaner spans than Stanza/UD, especially for institutional names:

```text
European Economic Community
Communauté économique européenne
Comunidad Económica Europea
Comunidade Económica Europeia
Council of Europe
Conselho da Europa
```

Its recall is much lower. The checkpoint also appears strongest on English, which is expected
because the model card says it was trained on English ACTER data. It still produced useful candidates
for German, French, Spanish, and Portuguese, but the output was sparse and occasionally partial, such
as `droits d`, `General`, or `Europeu`.

Use XLM-R/NOBI as a precision-oriented auxiliary extractor, not as the only extractor.

## Span-Based Model Feasibility Check

Two stronger span-based ideas were reviewed after the initial comparison:

- Feature-less End-to-End Nested Term Extraction.
- BINDER-style contrastive span/type extraction.

These are conceptually better aligned with the project than ordinary BIO tagging because both can
score overlapping spans. However, neither was kept in the codebase as a runnable extractor yet.

### Feature-Less Nested ATE

The public implementation is training code, not a ready multilingual checkpoint. It is useful as an
architecture reference, but we cannot fairly compare it on the five samples without first training or
fine-tuning a model.

Decision: do not add it as a current extractor. Revisit it when we build a supervised or silver-label
training set from verified benchmark terminology.

### BINDER

The official BINDER repository also provides training/evaluation code rather than a general
multilingual terminology checkpoint. A Hugging Face checkpoint,
`kristinalindquist/binder-biomedical-patents`, was tested as a quick feasibility check, but it did
not load as a reliable ready-to-use extractor in this environment. Transformers reported that many
weights were newly initialized, and the output was not terminology quality.

Observed output on a chemistry sentence included:

```text
chloride
thermal
products
decomposition
contains
sodium
solution
concentrated
formulation
The
```

The model returned isolated tokens and non-terms such as `contains` and `The`, so it failed the
quality threshold for candidate harvesting.

Decision: do not keep BINDER in the active comparison script or production terminology pipeline
until we have a correctly exported, trained checkpoint.

## Recommendation

The best current non-LLM setup is a union of:

```text
Stanza/UD candidates + XLM-R/NOBI candidates -> deduplicate -> external verifiers
```

Stanza/UD supplies recall. XLM-R/NOBI supplies cleaner high-precision spans. External verifiers
should decide which candidates become final benchmark terminology.
