# JRC Anchored Articles Terminology Quality Report

This report reviews terminology generated for the small anchored JRC-Acquis article dataset, grouped
by candidate extractor and verification status.

Dataset reviewed:

```text
benchmark_datasets/jrc_acquis_anchored_articles_5_all_non_llm_terms/
```

Combined manifest:

```text
benchmark_datasets/jrc_acquis_anchored_articles_5_all_non_llm_terms/jrc-acquis-20-directions-100-manifest.jsonl
```

## Dataset Summary

- Rows: 100.
- Directions: 20.
- Rows per direction: 5.
- Total terminology records: 1,919.
- Verified terminology records: 697.
- Non-verified terminology records: 1,222.
- Rows hitting the 20-term cap: 95 of 100.
- Target terms appearing exactly in target/reference text: 1,919 of 1,919.
- Records with populated `source_term`: 0 of 1,919.

## Pipeline Explanation

The JRC article benchmark starts from OPUS/JRC-Acquis aligned segments. The source builder selects
documents available in all required languages and expands each anchored chunk to every ordered
language pair. The dataset builder then writes `source.csv`, `target.csv`, and manifest rows per
direction.

Terminology is target-side:

```text
target/reference text
  -> Stanza/UD candidates
  -> XLM-R/NOBI candidates
  -> duplicate candidate merge
  -> external verifier lookup
  -> verified or non-verified manifest terms
```

Repeated anchored target chunks are deduplicated before extraction, so the same target-language chunk
is reused across multiple source-language directions.

## Method Explanations

Stanza/UD is the broad deterministic extractor. It proposes noun-headed dependency spans, relaxed
content n-grams, and proper-name sequences. It has high recall but produces the most legal
boilerplate, heading fragments, and table-of-contents noise.

XLM-R/NOBI is the neural extractor. It uses an XLM-R token-classification checkpoint with NOBI labels
for nested automatic term extraction. It produces fewer candidates and often cleaner named entities,
but it can still return generic single words.

LLM extraction is a prompt-based legal terminology extractor. In the LLM-only run, the model was
asked to extract exact target/reference spans, then the legal verifier layer was applied on top. This
mode was run separately from Stanza/UD and XLM-R/NOBI so its candidates can be inspected directly.

External verifiers add evidence to extracted candidates. Enabled sources were IATE,
Wikipedia/Wikidata, UNTERM, PubChem, ChEBI, ChEMBL, MeSH, NCI Thesaurus, and AGROVOC. Verification is
evidence, not automatic quality.

## Classes

Terms are split into six classes:

- `stanza_only + verified`
- `stanza_only + not_verified`
- `nobi_only + verified`
- `nobi_only + not_verified`
- `both + verified`
- `both + not_verified`

The compact table below gives record counts, unique-term counts, and frequency ranges. The term lists
after it show up to 100 extracted terms per class, ordered by frequency.

| Class | Records | Unique terms | 10+ repeats | 5-9 repeats | 2-4 repeats | 1 repeat |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stanza only, verified | 237 | 79 | 0 | 4 | 52 | 23 |
| Stanza only, not verified | 1,145 | 550 | 0 | 6 | 285 | 259 |
| NOBI only, verified | 376 | 109 | 3 | 4 | 80 | 22 |
| NOBI only, not verified | 58 | 20 | 0 | 0 | 15 | 5 |
| Stanza + NOBI, verified | 84 | 25 | 0 | 0 | 21 | 4 |
| Stanza + NOBI, not verified | 19 | 6 | 0 | 0 | 5 | 1 |

## Stanza Only, Verified

Terms:

`Partes Contratantes (7x)`; `Parte Contratante (7x)`; `Grupos Sanguíneos (7x)`; `Member States (5x)`; `Secretary-General (4x)`; `Contracting Parties (4x)`; `Contracting Party (4x)`; `MEMBER STATES (4x)`; `Additional Protocol (4x)`; `necessary measures (4x)`; `Blood-grouping (4x)`; `United Nations (4x)`; `Nations Conference (4x)`; `Council Regulation (4x)`; `Monitoring Centre (4x)`; `Management Board (4x)`; `Organización internacional (4x)`; `Comisión Europea (4x)`; `Unión Europea (4x)`; `instrument d'acceptation (4x)`; `parties contractantes (4x)`; `protocole additionnel (4x)`; `partie contractante (4x)`; `secrétaire général (4x)`; `partie intégrante (4x)`; `vice-président du Conseil (4x)`; `Admission d'observateurs (4x)`; `publication des comptes (4x)`; `Échange d'informations (4x)`; `mise à disposition (4x)`; `Protocolo Adicional (4x)`; `instrumento de aceitação (4x)`; `Organização Internacional (4x)`; `Nações Unidas (4x)`; `DISPOSIÇÕES FINANCEIRAS (4x)`; `relatório de avaliação (4x)`; `União Europeia (4x)`; `Comissão Europeia (4x)`; `personalidade independente (4x)`; `Intercâmbio de informações (4x)`; `Europäischen Union (4x)`; `sustancia de transición (3x)`; `países en desarrollo (3x)`; `medidas preventivas (3x)`; `Vereinten Nationen (3x)`; `Secretario General (3x)`; `ESTADOS MIEMBROS (3x)`; `Acuerdo Europeo (3x)`; `instrumento de aceptación (3x)`; `période de douze mois (3x)`; `Exchange of information (3x)`; `Controlled substance (2x)`; `precautionary measures (2x)`; `Transitional substance (2x)`; `capa de ozono (2x)`; `rationalisation industrielle (2x)`; `control measures (1x)`; `controlled substances (1x)`; `developing country (1x)`; `premier jour du mois (1x)`; `secrétaire général du Conseil de l'Europe (1x)`; `Tagung der Vertragsparteien (1x)`; `integración económica regional (1x)`; `Grupo II (1x)`; `Grupo I (1x)`; `regional economic integration organization (1x)`; `rendement économique (1x)`; `Organisation der regionalen Wirtschaftsintegration (1x)`; `innerstaatliche Rechtsvorschriften (1x)`; `eficiencia económica (1x)`; `Secretário-geral do Conselho da Europa (1x)`; `país em desenvolvimento (1x)`; `países em desenvolvimento (1x)`; `grupo I (1x)`; `Partes interesadas (1x)`; `materia prima (1x)`; `pays en développement (1x)`; `Communication des données (1x)`; `dix pour cent (1x)`.

Analysis:

This class is mostly useful legal terminology. The terms are often multiword and externally backed,
but some are still generic or context-dependent. This class should be kept, with light filtering and
ranking.

## Stanza Only, Not Verified

Terms:

`date d'entrée en vigueur du présent protocole (6x)`; `límites de producción (5x)`; `besoins intérieurs fondamentaux (5x)`; `Annex A (5x)`; `one or more of these substances (5x)`; `basic domestic needs of the Parties (5x)`; `notification o communication (4x)`; `following such signature (4x)`; `following the date (4x)`; `Contracting Party to the Agreement (4x)`; `one of the Contracting Parties (4x)`; `objection to the entry into force (4x)`; `integral part of the Agreement (4x)`; `Contracting Party to the Additional Protocol (4x)`; `recommendations of the Council (4x)`; `functions of the Council (4x)`; `Sessions of the Council (4x)`; `Quorum for the Council (4x)`; `Jute Organization (4x)`; `Annex B Shares (4x)`; `Jute Products (4x)`; `Annex B (4x)`; `objective of the Centre (4x)`; `Regulation (EC (4x)`; `purpose of the consultations (4x)`; `unnecessary duplication (4x)`; `Decisiones y recomendaciones del Consejo (4x)`; `vicepresidente del Consejo (4x)`; `CAPÍTULO III ORGANIZACIÓN (4x)`; `CAPÍTULO II DEFINICIONES (4x)`; `CAPÍTULO V PRIVILEGIOS (4x)`; `funciones del Consejo (4x)`; `14 Cooperación (4x)`; `CAPÍTULO IX (4x)`; `Consejo internacional (4x)`; `proyectos12 Artículo (4x)`; `objetivo del Observatorio (4x)`; `n° 1035/97 (4x)`; `Observatorio Europeo (4x)`; `HAN CONVENIDO (4x)`; `datos y trabajos de carácter confidencial realizados (4x)`; `coordinación de sus actividades (4x)`; `présent protocole additionnel (4x)`; `pouvoirs nécessaires (4x)`; `objection à l'entrée (4x)`; `mesures nécessaires (4x)`; `trait à l'accord (4x)`; `telle objection (4x)`; `acceptation ou objection au sens de l'article (4x)`; `réactifs pour la détermination des groupes (4x)`; `recommandations du Conseil (4x)`; `Notification d'application (4x)`; `CHAPITRE III ORGANISATION (4x)`; `Membres de l'Organisation (4x)`; `XI DISPOSITIONS DIVERSES (4x)`; `XII DISPOSITIONS FINALES (4x)`; `CHAPITRE II DÉFINITIONS (4x)`; `18 Comptes financiers (4x)`; `niveau calculé de production (4x)`; `niveau calculé de production de ces substances (4x)`; `coordination de leurs activités (4x)`; `objectif de l'Observatoire (4x)`; `consultations régulières (4x)`; `presente Protocolo Adicional (4x)`; `Acordo Europeu (4x)`; `Contratante no Acordo (4x)`; `medidas necessárias (4x)`; `uma das Partes Contratantes (4x)`; `reagentes para determinação de grupos (4x)`; `objecção à sua entrada em vigor (4x)`; `parte integrante do Acordo (4x)`; `nº 1 deste artigo (4x)`; `Parte Contratante no Protocolo Adicional (4x)`; `Conselho Internacional (4x)`; `vice-presidente do Conselho (4x)`; `CAPÍTULO III ORGANIZAÇÃO (4x)`; `ACTIVIDADES OPERACIONAIS (4x)`; `CAPÍTULO X ESTATÍSTICAS (4x)`; `CAPÍTULO II DEFINIÇÕES (4x)`; `CAPÍTULO V PRIVILÉGIOS (4x)`; `nível calculado de produção (4x)`; `CE) n.° 1035/97 (4x)`; `Observatório Europeu (4x)`; `coordenação das suas actividades (4x)`; `I. Intercâmbio de informações (4x)`; `informações objectivas (4x)`; `difusão tão vasta (4x)`; `Vertragspartei des Übereinkommens (4x)`; `Europäischen Übereinkommens (4x)`; `MITGLIEDSTAATEN DES EUROPARATS (4x)`; `Inkrafttretens dieses Zusatzprotokolls (4x)`; `Vertragspartei des Zusatzprotokolls (4x)`; `Einwand gegen sein Inkrafttreten (4x)`; `Generalsekretär des Europarats (4x)`; `letzte der Vertragsparteien (4x)`; `erforderlichen Befugnisse (4x)`; `menschlichen Ursprungs (4x)`; `notwendigen Maßnahmen (4x)`; `beigetretenen Staaten (4x)`; `Mitteilung im Zusammenhang mit diesem Übereinkommen (4x)`.

Analysis:

This is the largest and noisiest class. It contains useful recall candidates, but many terms are
headings, legal scaffolding, table-of-contents fragments, partial citations, or broad boilerplate.
This class should not be used as final benchmark terminology without strong filters.

## NOBI Only, Verified

Terms:

`JUTE (12x)`; `ECRI (12x)`; `industrial (10x)`; `Council (8x)`; `xenofobia (8x)`; `racismo (8x)`; `Adicional (7x)`; `Council of Europe (4x)`; `Protocol (4x)`; `Common Fund for Commodities (4x)`; `payment (4x)`; `account (4x)`; `Administrative account (4x)`; `Committee on projects (4x)`; `Financial accounts (4x)`; `European Monitoring Centre on Racism and Xenophobia (4x)`; `European Commission against Racism and Intolerance (4x)`; `Council of the European Union (4x)`; `anti-semitism (4x)`; `xenophobia (4x)`; `General (4x)`; `Organización internacional del yute (4x)`; `Consejo internacional del yute (4x)`; `Cuenta administrativa (4x)`; `Cuenta especial (4x)`; `fondo común (4x)`; `cuentas (4x)`; `YUTE (4x)`; `Cuentas financieras (4x)`; `Comisión Europea contra el racismo y la intolerancia (4x)`; `Observatorio Europeo del Racismo y la Xenofobia (4x)`; `Consejo de administración (4x)`; `antisemitismo (4x)`; `droits d (4x)`; `Conseil international du jute (4x)`; `fonds commun (4x)`; `comptes (4x)`; `paiement (4x)`; `Organisation internationale du jute (4x)`; `Comptes financiers (4x)`; `spécial (4x)`; `Observatoire européen des phénomènes racistes et xénophobes (4x)`; `Commission européenne contre le racisme et l'intolérance (4x)`; `administration (4x)`; `antisémitisme (4x)`; `xénophobie (4x)`; `racisme (4x)`; `règlement (4x)`; `général (4x)`; `Conseil d (4x)`; `Secretário-geral (4x)`; `Conselho Internacional da Juta (4x)`; `Comité dos projectos (4x)`; `Conta administrativa (4x)`; `Conta especial (4x)`; `Fundo comum (4x)`; `contas (4x)`; `JUTA (4x)`; `Comissão Europeia contra o Racismo e a Intolerância (4x)`; `Observatório Europeu do Racismo e da Xenofobia (4x)`; `anti-semitismo (4x)`; `CERI (4x)`; `Conselho de Administração (4x)`; `Verwaltungskonto (4x)`; `Sonderkonto (4x)`; `Zahlung (4x)`; `Finanzkonten (4x)`; `Europarat (4x)`; `emissions (3x)`; `emisiones (3x)`; `ozono (3x)`; `Conselho da Europa (3x)`; `Conseil de l'Europe (3x)`; `Commission (3x)`; `INTERNATIONAL JUTE COUNCIL (3x)`; `technologies (2x)`; `technical (2x)`; `ozone depletion (2x)`; `Consejo de Europa (2x)`; `capa de (2x)`; `Ozonschicht (2x)`; `Endziel (2x)`; `technische (2x)`; `CONSEJO DE EUROPA (2x)`; `tecnologías (2x)`; `industrielle (2x)`; `FCKW (2x)`; `technology (1x)`; `International Jute Council (1x)`; `accounts (1x)`; `Comunidad Económica Europea (1x)`; `integración económica regional (1x)`; `CONSEIL DE L'EUROPE (1x)`; `production (1x)`; `consommation (1x)`; `integração económica (1x)`; `DE OZONO (1x)`; `Europeu (1x)`; `produção (1x)`; `emissões (1x)`.

Analysis:

This class is mixed. It has strong named entities and domain terms, but also many generic verified
single words. Verification alone is not enough here. Generic terms such as `Council`, `industrial`,
`payment`, `account`, `Protocol`, and `General` should be down-ranked.

## NOBI Only, Not Verified

Terms:

`International Jute Organization (4x)`; `INTERNACIONAL DEL YUTE (4x)`; `INTERNACIONAL DA JUTA (4x)`; `executivo (4x)`; `Europarats (4x)`; `Gemeinsamen Fonds für Rohstoffe (4x)`; `FINANZFRAGEN (4x)`; `JUTEERZEUGNISSE (4x)`; `JUTERAT (4x)`; `Europäischen Kommission gegen Rassismus und Intoleranz (4x)`; `EKRI (4x)`; `MONTREAL (3x)`; `Isomere (2x)`; `regionalen Wirtschaftsintegration (2x)`; `técnicas (2x)`; `réduction de consommation (1x)`; `régionale d'intégration économique (1x)`; `Internationalen Juterats (1x)`; `Internationalen Juteorganisation (1x)`; `resepectivo (1x)`.

Analysis:

This class is small. Some terms are useful and simply missed by verifiers, while others are headings,
inflected fragments, or errors. It is useful for recall diagnostics and manual review, but not final
benchmark terminology.

## Stanza + NOBI, Verified

Terms:

`European Economic Community (4x)`; `European Community (4x)`; `Council of Europe (4x)`; `Consejo de la Unión Europea (4x)`; `Consejo de Europa (4x)`; `Comunidad Europea (4x)`; `Secretaría General (4x)`; `Communauté économique européenne (4x)`; `Compte administratif (4x)`; `Conseil de l'Union européenne (4x)`; `Communauté européenne (4x)`; `CONSEIL DE L'EUROPE (4x)`; `Comunidade Económica Europeia (4x)`; `Conselho da União Europeia (4x)`; `Comunidade Europeia (4x)`; `Conselho da Europa (4x)`; `Europäische Wirtschaftsgemeinschaft (4x)`; `Rat der Europäischen Union (4x)`; `Comunidad Económica Europea (3x)`; `Protocolo Adicional (3x)`; `OZONE LAYER (2x)`; `capa de ozono (1x)`; `economic integration (1x)`; `tetracloreto de carbono (1x)`; `Tétrachlorure de carbone (1x)`.

Analysis:

This is the strongest class. Agreement between both extractors plus external verification is the
best available signal. This class should receive the highest ranking priority.

## Stanza + NOBI, Not Verified

Terms:

`blood-grouping reagents (4x)`; `Europäischen Wirtschaftsgemeinschaft (4x)`; `Europäischen Gemeinschaft (4x)`; `Internationalen Juterats (3x)`; `Internationalen Juteorganisation (3x)`; `regionalen Wirtschaftsintegration (1x)`.

Analysis:

This class is small but promising. Agreement between both extractors means these terms are likely
salient, even when external verifiers do not match. This class should be kept for review and possible
source-term alignment.

## LLM Mode

The LLM-only article dataset was built from the same anchored article source and the same 5 rows per
direction. Stanza/UD and XLM-R/NOBI were disabled. LLM candidates were verified with the JRC legal
verifier layer: IATE, Wikipedia/Wikidata, and UNTERM.

LLM mode summary:

- Rows: 100.
- Total terminology records: 1,628.
- Verified records: 798.
- Non-verified records: 830.
- Unique verified terms: 272.
- Unique non-verified terms: 389.
- Records with populated `source_term`: 0 of 1,628.

| LLM class | Records | Unique terms | 10+ repeats | 5-9 repeats | 2-4 repeats | 1 repeat |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LLM, verified | 798 | 272 | 2 | 14 | 174 | 82 |
| LLM, not verified | 830 | 389 | 0 | 14 | 172 | 203 |

### LLM, Verified

Terms:

`ECRI (12x)`; `Vertragsparteien (10x)`; `Protocolo (9x)`; `notification (8x)`; `PROTOCOLO ADICIONAL (8x)`; `Partes Contratantes (8x)`; `protocole (8x)`; `Inkrafttreten (6x)`; `entry into force (5x)`; `transferir (5x)`; `Consejo de Europa (5x)`; `Parte Contratante (5x)`; `Conselho da Europa (5x)`; `Protokoll (5x)`; `Produktion (5x)`; `Sekretariat (5x)`; `European Economic Community (4x)`; `ADDITIONAL PROTOCOL (4x)`; `Contracting Parties (4x)`; `instrument of acceptance (4x)`; `acceptance (4x)`; `Treaty (4x)`; `Common Fund for Commodities (4x)`; `International Jute Council (4x)`; `Privileges and immunities (4x)`; `Depositary (4x)`; `Notification of provisional application (4x)`; `Audit and publication of accounts (4x)`; `Relief from obligations (4x)`; `Committee on projects (4x)`; `Financial accounts (4x)`; `Special account (4x)`; `European Monitoring Centre on Racism and Xenophobia (4x)`; `European Commission against Racism and Intolerance (4x)`; `Council of Europe (4x)`; `AGREEMENT (4x)`; `Centre (4x)`; `confidential data (4x)`; `Management Board (4x)`; `work programme (4x)`; `Comunidad Económica Europea (4x)`; `ACUERDO EUROPEO (4x)`; `instrumento de aceptación (4x)`; `derechos de importación (4x)`; `Tratado constitutivo (4x)`; `entrada en vigor (4x)`; `notificación (4x)`; `aceptación (4x)`; `objeción (4x)`; `FONDO COMÚN PARA LOS PRODUCTOS BÁSICOS (4x)`; `Organización internacional del yute (4x)`; `Consejo internacional del yute (4x)`; `Privilegios e inmunidades (4x)`; `Comité de proyectos (4x)`; `Depositario (4x)`; `Cuentas financieras (4x)`; `Observatorio Europeo del Racismo y la Xenofobia (4x)`; `Comunidad Europea (4x)`; `Observatorio (4x)`; `ACUERDO (4x)`; `Intercambio de información y de datos (4x)`; `Communauté économique européenne (4x)`; `PROTOCOLE ADDITIONNEL (4x)`; `entrée en vigueur (4x)`; `ACCORD EUROPÉEN (4x)`; `instrument d'acceptation (4x)`; `parties contractantes (4x)`; `signature (4x)`; `traité (4x)`; `Organisation internationale du jute (4x)`; `Conseil international du jute (4x)`; `Privilèges et immunités (4x)`; `Dépositaire (4x)`; `Comité des projets (4x)`; `Adhésion (4x)`; `Compte administratif (4x)`; `Comptes financiers (4x)`; `Compte spécial (4x)`; `Observatoire européen des phénomènes racistes et xénophobes (4x)`; `Commission européenne contre le racisme et l'intolérance (4x)`; `Communauté européenne (4x)`; `Conseil de l'Europe (4x)`; `Observatoire (4x)`; `ACCORD (4x)`; `programme d'activité (4x)`; `Comunidade Económica Europeia (4x)`; `entrada em vigor (4x)`; `instrumento de aceitação (4x)`; `notificação (4x)`; `aceitação (4x)`; `objecção (4x)`; `Tratado (4x)`; `ACORDO INTERNACIONAL DE 1989 SOBRE A JUTA E OS ARTIGOS DE JUTA (4x)`; `Fundo comum para os produtos de base (4x)`; `Organização Internacional da Juta (4x)`; `Conselho Internacional da Juta (4x)`; `Privilégios e imunidades (4x)`; `Entrada em vigor (4x)`; `Denúncia (4x)`; `Comité dos projectos (4x)`.

Analysis:

The LLM verified group is broader and often more semantically meaningful than raw Stanza-only output.
It captures many legal headings and institutional terms in complete phrases. However, it still
contains generic or structurally weak terms such as `notification`, `acceptance`, `signature`,
`AGREEMENT`, `ACCORD`, `Centre`, and `Observatoire`. The LLM helps phrase quality, but verifier
evidence is still not enough to guarantee technical difficulty.

### LLM, Not Verified

Terms:

`Partes (9x)`; `anexo A (8x)`; `substances réglementées (8x)`; `anexo B (7x)`; `niveau calculé de production (7x)`; `substâncias regulamentadas (7x)`; `controlled substances (6x)`; `nível calculado de produção (6x)`; `sustancias controladas (5x)`; `parties (5x)`; `niveau calculé de consommation (5x)`; `besoins intérieurs fondamentaux (5x)`; `nível calculado de consumo (5x)`; `calculated level of production (5x)`; `Secretary-General of the Council of Europe (4x)`; `MEMBER STATES OF THE COUNCIL OF EUROPE (4x)`; `EUROPEAN AGREEMENT (4x)`; `objection to the entry into force (4x)`; `exempt from all import duties (4x)`; `acceded to the Agreement (4x)`; `import duties (4x)`; `exchanges of blood-grouping reagents (4x)`; `Signature, ratification, acceptance and approval (4x)`; `International Jute Organization (4x)`; `General obligations of members (4x)`; `Differential and remedial measures (4x)`; `Complaints and disputes (4x)`; `Annex A (4x)`; `Annex B (4x)`; `Council Regulation (EC) No 1035/97 (4x)`; `joint and/or complementary activities (4x)`; `Exchange of information and data (4x)`; `Secretario General del Consejo de Europa (4x)`; `nivel calculado de producción (4x)`; `Firma, ratificación, aceptación y aprobación (4x)`; `Obligaciones generales de los miembros (4x)`; `Procedimiento de votación del Consejo (4x)`; `Auditoría y publicación de cuentas (4x)`; `Quórum del Consejo (4x)`; `Decisiones y recomendaciones del Consejo (4x)`; `Medidas diferenciales y correctivas (4x)`; `Facultades y funciones del Consejo (4x)`; `Reclamaciones y controversias (4x)`; `anexo C (4x)`; `Reglamento (CE) n° 1035/97 (4x)`; `Comisión Europea contra el racismo y la intolerancia (ECRI (4x)`; `Consejo de administración del Observatorio (4x)`; `programa de trabajo del Observatorio (4x)`; `secrétaire général du Conseil de l'Europe (4x)`; `objection à l'entrée en vigueur (4x)`; `droits d'importation (4x)`; `ACCORD INTERNATIONAL DE 1989 SUR LE JUTE ET LES ARTICLES EN JUTE (4x)`; `Signature, ratification, acceptation et approbation (4x)`; `Obligations générales des membres (4x)`; `Plaintes et différends (4x)`; `Modes de paiement (4x)`; `règlement (CE) n° 1035/97 (4x)`; `mise à disposition réciproque des informations et données (4x)`; `coordination de leurs activités (4x)`; `Secretário-geral do Conselho da Europa (4x)`; `ACORDO EUROPEU (4x)`; `direitos de importação (4x)`; `Obrigações gerais dos membros (4x)`; `Assinatura, ratificação, aceitação e aprovação (4x)`; `Duração, prorrogação e fim do acordo (4x)`; `Queixas e diferendos (4x)`; `Regulamento (CE) n.° 1035/97 (4x)`; `Comissão Europeia contra o Racismo e a Intolerância (CERI (4x)`; `Conselho de Administração do Observatório (4x)`; `Intercâmbio de informações e de dados (4x)`; `coordenação das suas actividades (4x)`; `Mitgliedstaaten der Europäischen Wirtschaftsgemeinschaft (4x)`; `Generalsekretär des Europarats (4x)`; `EUROPÄISCHEN ÜBEREINKOMMEN (4x)`; `Verpflichtung zur Gewährung dieser Befreiung (4x)`; `Artikel 5 Absatz 1 des Übereinkommens (4x)`; `therapeutischen Substanzen menschlichen Ursprungs (4x)`; `Einwand gegen sein Inkrafttreten (4x)`; `Eingangsabgaben (4x)`; `Allgemeine Verpflichtungen der Mitglieder (4x)`; `Mitgliedschaft zwischenstaatlicher Organisationen (4x)`; `Mitgliedschaft in der Organisation (4x)`; `Beschwerden und Streitigkeiten (4x)`; `Befugnisse und Aufgaben des Rates (4x)`; `Produktionsgrenzen (4x)`; `Verordnung (EG) Nr. 1035/97 (4x)`; `Informations- und Datenaustausch (4x)`; `Mitglied des Verwaltungsrates (4x)`; `Article 2 C (4x)`; `calculated level of consumption (4x)`; `communication relating to the Agreement (3x)`; `production limits (3x)`; `período de dos años (3x)`; `CONVENIO INTERNACIONAL DEL YUTE Y LOS PRODUCTOS DEL YUTE, 1989 (3x)`; `ENMIENDA AL PROTOCOLO DE MONTREAL (3x)`; `períodos de control (3x)`; `recipiente utilizado para el transporte o almacenamiento (3x)`; `puesta a disposición recíproca (3x)`; `coordinación de sus actividades (3x)`; `transfert de production (3x)`.

Analysis:

The LLM non-verified group contains many of the best technical-looking terms, including `controlled
substances`, `substances réglementées`, `calculated level of production`, and `Council Regulation
(EC) No 1035/97`. The lack of verification does not mean low quality. It often means the term is a
longer legal/technical phrase or an inflected multilingual phrase that the verifier did not match
exactly. This group is better than Stanza-only non-verified terms and should be reviewed carefully.

### LLM Mode Takeaway

LLM mode is better at producing coherent legal and technical phrases than the raw non-LLM extractors.
Its non-verified terms are often more useful than non-verified Stanza-only terms. The weakness is
that it can still include headings and generic legal words, and it still does not populate
`source_term`.

## Main Points

1. The best class is `Stanza + NOBI, verified`.
2. The worst large class is `Stanza only, not verified`.
3. `NOBI only, verified` is useful but needs generic single-word filtering.
4. `Stanza + NOBI, not verified` is small and worth manual review.
5. `LLM, not verified` contains many coherent technical phrases that exact-match verifiers miss.
6. Verification helps, but it does not guarantee benchmark-quality terminology.
7. The current terms are target-side only because `source_term` is empty.

## Recommendations

1. Rank `Stanza + NOBI, verified` highest.
2. Use LLM mode as a quality-oriented phrase proposer, especially for longer legal/technical terms.
3. Prefer verified multiword terms over verified single words.
4. Penalize generic verified words such as `Council`, `Protocol`, `payment`, `account`,
   `industrial`, `General`, and `Adicional`.
5. Keep `Stanza + NOBI, not verified` and `LLM, not verified` as review buckets.
6. Treat `Stanza only, not verified` as a recall/diagnostic bucket, not final terminology.
7. Add filters for headings, table-of-contents spans, article references, malformed citations, and
   partial spans ending in function words.
8. Populate `source_term` by aligning accepted target terms back to source text.
9. Regenerate the 5-row sample after filtering/ranking changes before scaling to 250.

## Improving Technical Difficulty

The current pipeline produces many valid terms, but not all are technically difficult enough for a
strong terminology-sensitive benchmark. The next improvement should be a technical term
ranker/filter before final term selection.

Preferred signals:

- Found by both Stanza/UD and XLM-R/NOBI.
- Verified by at least one external source.
- Verified by multiple external sources.
- Multiword span, especially 2-6 tokens.
- Legal, institutional, scientific, chemical, or regulatory phrase.
- Acronym or formal entity name, such as `ECRI`, `JUTE`, or `FCKW`.
- Domain-bearing words such as `ozone`, `substance`, `carbon`, `economic integration`,
  `administrative account`, `monitoring centre`, or equivalent multilingual forms.

Penalty signals:

- Generic single word, such as `Council`, `Protocol`, `payment`, `account`, `industrial`,
  `General`, or `Adicional`.
- Heading or table-of-contents text.
- Article/paragraph numbering.
- Partial spans ending in function words, such as `droits d` or `Conseil d`.
- Malformed spans, dot leaders, OCR artifacts, or punctuation fragments.

Recommended scoring shape:

```text
technical_score =
  + both_extractors
  + verified
  + multiple_verifiers
  + multiword
  + domain_or_institution_pattern
  + acronym_or_formula_pattern
  - generic_single_word
  - heading_or_toc_pattern
  - article_or_numbering_pattern
  - partial_or_malformed_span
```

The final manifest should keep fewer, harder terms rather than filling every row with 20 broad
candidates. A better target is something like:

- top 5 verified technical terms per row;
- plus top 2 `Stanza + NOBI, not verified` terms for review;
- no generic verified single words unless they are acronyms, formulas, or clear domain terms.

The largest quality gain will come from populating `source_term`. A term is much more useful for
translation benchmarking if both the source span and target span are known, not only the target-side
reference span.
