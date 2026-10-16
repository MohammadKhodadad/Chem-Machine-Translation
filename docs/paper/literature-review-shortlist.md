# Literature review: translation capability and multilingual domain benchmarking

Research date: 2026-10-16. Exactly 20 candidate papers, selected for a translation-capability study: multilingual chemical patent prose as the primary benchmark, legal text as a comparison domain, general translation evaluation, and terminology metrics as a complementary contribution. Source-only translation is the primary condition; reference-derived oracle target-term prompting is a separate assisted condition.

## Recommended argument

Follow a broad-to-specific narrative: existing work on translation with LLMs; translation benchmarks, particularly WMT25; metrics for comparing model performance, including terminology accuracy; a short discussion of terminology extraction; and finally the target domain, chemical-patent prose, with legal translation as a comparison domain. Keep the numbered catalogue stable for citation lookup; the paragraph plan and draft below define the reading order.

The central question is how well translation systems translate specialized prose across languages and domains, not primarily whether they follow a glossary. Position the paper as a controlled translation-capability benchmark, with a provenance-preserving evaluation resource and terminology metrics that reveal one domain-important dimension of performance alongside general quality. Compare systems on the same held-out segments and language directions; report direction-level and domain-level results rather than relying only on a pooled ranking. Chemical entity recognition and molecular notation conversion provide domain context, but neither is equivalent to multilingual chemical prose translation.

The intended contribution hierarchy is: (1) a multilingual domain-specific translation benchmark and reproducible comparison protocol; (2) an empirical assessment of translation capability, including strengths and failures across directions and domains; and (3) complementary terminology metrics and annotation provenance. These are intended contributions, not claims of completed results or established novelty. Terminology-assisted translation is an auxiliary controlled experiment: reference-derived oracle assistance must remain separate from realistic source-only translation and must not determine the headline capability ranking.

This is a targeted research shortlist, not a systematic review or proof that no similar benchmark exists. Metadata and the claims below were checked against linked primary publication records and abstracts. Full text was additionally accessible for papers 11 and 12 through Europe PMC. Direct PDF extraction failed for papers 6, 8, and 10; their summaries deliberately stay within their official abstracts. No quantitative result from those PDFs is assumed. Suggested wording is original paraphrase, not a quotation.

## How to use one page

Aim for approximately 500-600 words excluding references; the exact page fit depends on the template. Organize by research question, not one paragraph per paper. The draft below uses all 20 as grouped citations, but it is reasonable to move the routine metric and corpus citations to Methods if space is tight.

| Paragraph | Purpose | Papers | Approximate words |
| --- | --- | --- | --- |
| 1 | Establish existing LLM translation research, prompting, and adaptation | 1, 4-5 | 80-100 |
| 2 | Introduce multilingual benchmarking and WMT25's challenging evaluation settings | 2-3 | 90-110 |
| 3 | Compare model performance with general metrics, expert assessment, and terminology accuracy | 7, 9, 15-20 | 130-150 |
| 4 | Briefly explain terminology extraction as an annotation dependency | 10 | 40-60 |
| 5 | Narrow to chemical-patent translation, adjacent chemistry tasks, and legal comparison work | 6, 8, 11-14 | 140-160 |

Priority reading: 1, 2, 3, 4, 18, 20. These establish translation capability, benchmark design, and general-quality assessment. Papers 6-9 support the terminology contribution; papers 10-14 support annotation and domain/resource context. Routine metric and corpus citations can move to Methods before cutting the central capability/benchmarking discussion.

## A. Translation capability, benchmarking, and adaptation

### 1. Hendy et al. (2023): comprehensive GPT translation evaluation

**Citation:** Amr Hendy et al. *How Good Are GPT Models at Machine Translation? A Comprehensive Evaluation*. arXiv preprint (2023). [Primary record and paper](https://arxiv.org/abs/2302.09210). DOI: 10.48550/arXiv.2302.09210.

- **Verified contribution:** Evaluates three GPT systems across 18 translation directions against research and commercial systems, examining prompting, domain shifts, document translation, and human assessments. Reports competitive high-resource performance and limitations on low-resource languages in the tested setup.
- **Why it belongs:** Direct precedent for assessing translation capability across systems and conditions rather than making terminology compliance the central task.
- **What we should say:** "Comprehensive GPT evaluations find that translation capability varies with language resources and experimental conditions, motivating direction-specific assessment against established translation systems."
- **Boundary:** A 2023 preprint about particular GPT versions, not evidence about every current model or our chemistry benchmark. Its domain-shift experiments do not establish chemical-patent performance.
- **Placement:** Paragraph 1; central translation-capability reference.

### 2. Goyal et al. (2022): FLORES-101 multilingual benchmark

**Citation:** Naman Goyal et al. *The Flores-101 Evaluation Benchmark for Low-Resource and Multilingual Machine Translation*. TACL 10 (2022), 522-538. [Publication and PDF](https://aclanthology.org/2022.tacl-1.30/). DOI: 10.1162/tacl_a_00474.

- **Verified contribution:** Introduces 3,001 sentences originating in English Wikipedia, professionally translated into 101 languages through a controlled process. Fully aligned translations enable many-to-many multilingual evaluation.
- **Why it belongs:** Establishes shared evaluation content and reference quality as benchmark-design concerns, directly relevant to comparing language directions on common anchors.
- **What we should say:** "FLORES-101 provides professionally translated, fully aligned multilingual evaluation data, enabling controlled many-to-many comparisons."
- **Boundary:** Our corpus-derived references and automatic annotations do not inherit FLORES's professional translation quality assurance. Shared anchors support comparability but do not eliminate translationese, alignment errors, or domain differences.
- **Placement:** Paragraph 2; central benchmark-design reference.

### 3. Kocmi et al. (2025): WMT25 general translation benchmarking

**Citation:** Tom Kocmi et al. *Findings of the WMT25 General Machine Translation Shared Task: Time to Stop Evaluating on Easy Test Sets*. WMT 2025, 355-413. [Publication and PDF](https://aclanthology.org/2025.wmt-1.22/). DOI: 10.18653/v1/2025.wmt-1.22.

- **Verified contribution:** Invites participation for 30 language pairs and conducts human evaluation for half of them on four to five domains. Evaluates 60 systems: 36 submissions and 24 LLM/online-provider systems. Introduces difficulty sampling and more complex source data; professional assessment uses ESA except for two pairs evaluated with MQM. Supplies whole-document source context.
- **Why it belongs:** Recent broad model-comparison template linking translation capability to test difficulty, domain coverage, system diversity, and evaluation context.
- **What we should say:** "WMT25 benchmarks submitted systems, LLMs, and online providers on challenging multilingual test sets, emphasizing test difficulty, domain coverage, and document context."
- **Boundary:** Do not say all 30 pairs received human evaluation. Our segment-level benchmark does not reproduce WMT25's difficulty sampling, document-level setup, or professional ESA/MQM protocols. Its rankings do not establish chemical-patent performance.
- **Placement:** Paragraph 2; central translation-benchmark reference, after introducing LLM translation research.

### 4. Vilar et al. (2023): prompting PaLM for MT

**Citation:** David Vilar, Markus Freitag, Colin Cherry, Jiaming Luo, Viresh Ratnakar, and George Foster. *Prompting PaLM for Translation: Assessing Strategies and Performance*. ACL 2023, 15406-15427. [Publication and PDF](https://aclanthology.org/2023.acl-long.859/). DOI: 10.18653/v1/2023.acl-long.859.

- **Verified contribution:** Studies few-shot example selection, finding example quality especially important; optimized PaLM prompting still trails the supervised state of the art in the reported evaluation.
- **Why it belongs:** Grounds prompt design and cautions against treating general LLM translation capability as evidence of domain fidelity.
- **What we should say:** "LLM translation performance depends on prompting choices, including the quality of supplied examples, and strong prompting does not by itself establish superiority over supervised MT."
- **Boundary:** The findings concern the tested PaLM system and conditions, not every later LLM. We currently inject terms, not retrieved translation demonstrations.
- **Placement:** Paragraph 1; general LLM-MT context.

### 5. Moslem et al. (2023): adaptive LLM translation

**Citation:** Yasmin Moslem, Rejwanul Haque, John D. Kelleher, and Andy Way. *Adaptive Machine Translation with Large Language Models*. EAMT 2023, 227-237. [Publication and PDF](https://aclanthology.org/2023.eamt-1.22/).

- **Verified contribution:** Investigates in-context adaptation using in-domain sentence pairs and/or terminology, including combinations with fuzzy matches and encoder-decoder MT across five language pairs.
- **Why it belongs:** Direct precedent for inference-time translation assistance without fine-tuning the model for each project.
- **What we should say:** "In-context adaptation can condition LLM translation on in-domain examples and terminology, with gains dependent on language and assistance configuration."
- **Boundary:** Their example/terminology-assisted conditions are not interchangeable with our reference-derived target-only term lists. Do not call our current system retrieval-augmented MT.
- **Placement:** Paragraph 1; direct methodological neighbor.

### 6. Di Natale et al. (2025): LegISTyr

**Citation:** Paolo Di Natale, Egon W. Stemle, Elena Chiocchetti, Marlies Alber, Natascia Ralli, Isabella Stanizzi, and Elena Benini. *The LegISTyr Test Set: Investigating Off-the-Shelf Instruction-Tuned LLMs for Terminology-Constrained Translation in a Low-Resource Language Variety*. TermTrends 2025, 1-15. [Publication and PDF](https://aclanthology.org/2025.termtrends-1.1/).

- **Verified contribution:** Releases 2,000 manually curated Italian legal sentences with Italian/South Tyrolean German terminology, including homonym challenges; compares translation-specialized LLMs, generic LLMs, and NMT systems. The abstract distinguishes raw term insertion from fluency and homonym selection.
- **Why it belongs:** One of the closest comparators: legal translation, supplied terminology, off-the-shelf LLMs, and terminology-focused evaluation.
- **What we should say:** "LegISTyr evaluates terminology injection in Italian-to-South-Tyrolean-German legal translation and shows why raw insertion rates must be distinguished from contextual lexical choice and overall quality."
- **Boundary:** Our legal data are not manually curated like LegISTyr, and our reference-only term annotations do not provide its bilingual homonym test. A different language roster alone is not proof of a novel method.
- **Placement:** Paragraph 5; legal-domain comparator for the auxiliary terminology-assisted experiment.

## B. Terminology-specific evaluation and annotation

### 7. Alam et al. (2021): WMT terminology shared task

**Citation:** Md Mahfuz Ibn Alam et al. *Findings of the WMT Shared Task on Machine Translation Using Terminologies*. WMT 2021, 652-663. [Publication and PDF](https://aclanthology.org/2021.wmt-1.69/).

- **Verified contribution:** Introduces a medical/COVID-19 terminology translation benchmark covering five language pairs and reports participating systems, highlighting unresolved task formulation and evaluation issues.
- **Why it belongs:** Establishes that terminology translation quality and consistency already have dedicated multilingual benchmarking precedents.
- **What we should say:** "The WMT terminology shared task established a multilingual medical benchmark and identified continuing challenges in terminology handling and its evaluation."
- **Boundary:** Medical/COVID-19 terminology is adjacent to, not equivalent to, chemistry patent terminology. Our term-presence coverage is not a reproduction of the shared-task protocol.
- **Placement:** Paragraph 3; prior terminology benchmark supporting terminology-specific evaluation.

### 8. Hauksdottir and Steingrimsson (2025): EEA terminology test suite

**Citation:** Selma Dis Hauksdottir and Steinthor Steingrimsson. *Automated Evaluation for Terminology Translation Related to the EEA Agreement*. WMT 2025, 850-855. [Publication and PDF](https://aclanthology.org/2025.wmt-1.59/). DOI: 10.18653/v1/2025.wmt-1.59.

- **Verified contribution:** Evaluates English-Icelandic terminology in EEA documents across four domains; reports manual confirmation of test-suite usefulness and a mismatch between general-task standing and terminology performance for an online system.
- **Why it belongs:** Concrete legal-domain evidence for evaluating terminology separately from overall MT quality.
- **What we should say:** "An EEA terminology test suite finds that terminology-specific performance need not follow general MT rankings, motivating separate reporting."
- **Boundary:** This is a finding in that test suite, not proof that all general metrics always fail or that our own rankings will differ. Icelandic is outside our current legal language roster.
- **Placement:** Paragraph 5; legal-domain evidence for a complementary diagnostic.

### 9. Dahan et al. (2026): valid terminology variation

**Citation:** Nicolas Dahan, Ziqian Peng, Francois Yvon, and Rachel Bawden. *Improving Term Evaluation in Machine Translation: Variation Matters*. AMTA 2026, research track, 101-134. [Publication and PDF](https://aclanthology.org/2026.amta-research.7/).

- **Verified contribution:** Studies English-French scientific document translation using glossary accuracy, consistency, and cross-term variation. Reports that glossary constraints can improve accuracy/consistency while suppressing valid variation, and that metric choice affects consistency rankings.
- **Why it belongs:** Directly challenges the assumption that matching a single reference term or maximizing consistency is sufficient.
- **What we should say:** "Variation-aware evaluation distinguishes undesirable inconsistency from legitimate alternative renderings; glossary compliance and preservation of source-side variation can trade off."
- **Boundary:** Our stored-variant coverage is narrower than their document-level, source-conditioned variation analysis. Neither generic synonyms nor case folding establish chemical equivalence.
- **Placement:** Paragraph 3; qualification of terminology accuracy and consistency metrics.

### 10. Chun et al. (2025): syntactic retrieval for term extraction

**Citation:** Yongchan Chun, Minhyuk Kim, Dongjun Kim, Chanjun Park, and Heuiseok Lim. *Enhancing Automatic Term Extraction with Large Language Models via Syntactic Retrieval*. Findings of ACL 2025, 9916-9926. [Publication and PDF](https://aclanthology.org/2025.findings-acl.516/). DOI: 10.18653/v1/2025.findings-acl.516.

- **Verified contribution:** Selects few-shot demonstrations by syntactic rather than semantic similarity to guide term boundaries; reports improved extraction F1 on three specialized benchmarks in in-domain and cross-domain settings.
- **Why it belongs:** Recent precedent for combining linguistic information with LLM-based term extraction, relevant to our multiple candidate sources.
- **What we should say:** "Recent LLM-based term extraction exploits syntactic demonstration retrieval to improve term-boundary prediction across specialized benchmarks."
- **Boundary:** We do not implement their retrieval method, and their F1 results do not validate our ensemble. Exact-span checks establish reference occurrence, not annotation precision or completeness.
- **Placement:** Paragraph 4; annotation motivation, not a claim of implementing their method.

## C. Chemistry and multilingual resources

### 11. Rajan, Zielesny, and Steinbeck (2021): STOUT

**Citation:** Kohulan Rajan, Achim Zielesny, and Christoph Steinbeck. *STOUT: SMILES to IUPAC names using neural machine translation*. Journal of Cheminformatics 13, article 34 (2021). [Full text](https://europepmc.org/articles/PMC8077691). [DOI](https://doi.org/10.1186/s13321-021-00512-4).

- **Verified contribution:** Learns chemical representation/name conversion using molecular strings and IUPAC names; evaluates sequence overlap alongside OPSIN-based reconversion, fingerprint similarity, and structural comparisons. The implementation uses SELFIES as an intermediate representation.
- **Why it belongs:** Gives chemistry-specific evidence that string similarity and chemical structure preservation are distinct evaluation targets.
- **What we should say:** "STOUT addresses molecular representation-to-name conversion and complements sequence scores with structure-oriented checks, illustrating why textual similarity is not equivalent to chemical identity."
- **Boundary:** Not multilingual prose MT. Fingerprint similarity of 1 is not universally proof of molecular identity; their paper separately examines graph equivalence. We have not implemented these structure checks.
- **Placement:** Paragraph 5; chemistry context, explicitly adjacent rather than directly comparable.

### 12. Krallinger et al. (2015): CHEMDNER challenge

**Citation:** Martin Krallinger, Florian Leitner, Obdulia Rabal, Miguel Vazquez, Julen Oyarzabal, and Alfonso Valencia. *CHEMDNER: The drugs and chemical names extraction challenge*. Journal of Cheminformatics 7 (Suppl 1), S1 (2015). [Full text](https://europepmc.org/articles/PMC4331685). [DOI](https://doi.org/10.1186/1758-2946-7-S1-S1).

- **Verified contribution:** Benchmarks chemical document indexing and exact chemical mention recognition against expert annotations, with explicit mention boundaries and precision/recall/F1. Discusses naming variation, ambiguity, and tokenization difficulties; structure grounding is outside the challenge scope.
- **Why it belongs:** Establishes an expert-annotated standard for evaluating chemical span extraction, highlighting what our automatic annotations do not yet demonstrate.
- **What we should say:** "CHEMDNER evaluates chemical mention recognition against expert annotations, separating span detection from the distinct problem of structure grounding."
- **Boundary:** Chemical entity recognition is not bilingual terminology translation, and chemical names are only part of our broader process/material terminology. Do not label our automatic manifests expert gold data.
- **Placement:** Paragraph 5; chemical annotation context and honest limitation.

### 13. Steinberger et al. (2006): JRC-Acquis

**Citation:** Ralf Steinberger et al. *The JRC-Acquis: A Multilingual Aligned Parallel Corpus with 20+ Languages*. LREC 2006. [Publication and PDF](https://aclanthology.org/L06-1196/).

- **Verified contribution:** Releases multilingual, predominantly legal EU documents with pairwise alignment information, supporting cross-language research and benchmarking.
- **Why it belongs:** Primary scholarly attribution for our legal comparison corpus.
- **What we should say:** "JRC-Acquis provides multilingual legal parallel text for evaluating transfer to a second terminology-sensitive domain."
- **Boundary:** The original corpus paper does not establish the quality of our selected chunks, definition filtering, or newly generated terminology annotations. JRC is not chemical training data.
- **Placement:** Paragraph 5 or Data; cite alongside paper 14.

### 14. Tiedemann (2012): OPUS

**Citation:** Jorg Tiedemann. *Parallel Data, Tools and Interfaces in OPUS*. LREC 2012, 2214-2218. [Publication and PDF](https://aclanthology.org/L12-1246/).

- **Verified contribution:** Describes OPUS parallel corpora, distribution formats, annotation tools, and interfaces.
- **Why it belongs:** Attributes the parallel-data infrastructure through which we obtain the JRC aligned text.
- **What we should say:** "We use the OPUS distribution of JRC-Acquis, building our evaluation snapshot on established parallel-corpus infrastructure."
- **Boundary:** Cite JRC and OPUS separately for corpus origin and distribution. This 2012 paper is not documentation of every property of the particular v3.0 snapshot; version and checksums belong in Methods.
- **Placement:** Paragraph 5 or Data; resource attribution, not methodological novelty.

## D. General translation evaluation

### 15. Papineni et al. (2002): BLEU

**Citation:** Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. *Bleu: a Method for Automatic Evaluation of Machine Translation*. ACL 2002, 311-318. [Publication and PDF](https://aclanthology.org/P02-1040/). DOI: 10.3115/1073083.1073135.

- **Verified contribution:** Introduces the foundational reference-overlap MT metric based on modified n-gram precision and a brevity penalty.
- **Why it belongs:** Establishes the conventional lexical baseline that our terminology diagnostic complements.
- **What we should say:** "BLEU measures reference n-gram overlap, providing a general lexical evaluation rather than an explicit terminology audit."
- **Boundary:** Do not claim the BLEU paper evaluates chemical errors. Aggregate overlap cannot certify chemical identity; this is a task-design distinction, not a chemistry experiment reported in this paper.
- **Placement:** Paragraph 3 or Evaluation; group with papers 16-19.

### 16. Post (2018): SacreBLEU and reproducibility

**Citation:** Matt Post. *A Call for Clarity in Reporting BLEU Scores*. WMT 2018, 186-191. [Publication and PDF](https://aclanthology.org/W18-6319/). DOI: 10.18653/v1/W18-6319.

- **Verified contribution:** Demonstrates that BLEU configuration and reference preprocessing affect reported scores; introduces SacreBLEU to standardize scoring.
- **Why it belongs:** Supports reproducible tokenization, normalization, and metric reporting across languages and systems.
- **What we should say:** "SacreBLEU addresses comparability problems caused by inconsistent BLEU parameterization and reference preprocessing."
- **Boundary:** Standardization improves reproducibility, not sensitivity to chemical identity or terminology correctness.
- **Placement:** Paragraph 3 or Evaluation; one grouped citation is enough.

### 17. Popovic (2017): chrF++

**Citation:** Maja Popovic. *chrF++: words helping character n-grams*. WMT 2017, 612-618. [Publication and PDF](https://aclanthology.org/W17-4770/). DOI: 10.18653/v1/W17-4770.

- **Verified contribution:** Combines character and word n-gram matching in the chrF family of MT evaluation measures.
- **Why it belongs:** Adds a complementary surface-overlap view beyond word-only BLEU.
- **What we should say:** "chrF++ combines character and word overlap, complementing word-based lexical evaluation."
- **Boundary:** Character overlap can remain high for a chemically important small edit; this paper does not validate chrF++ as a molecular correctness measure.
- **Placement:** Paragraph 3 or Evaluation.

### 18. Rei et al. (2020): COMET

**Citation:** Ricardo Rei, Craig Stewart, Ana C Farinha, and Alon Lavie. *COMET: A Neural Framework for MT Evaluation*. EMNLP 2020, 2685-2702. [Publication and PDF](https://aclanthology.org/2020.emnlp-main.213/). DOI: 10.18653/v1/2020.emnlp-main.213.

- **Verified contribution:** Learns multilingual quality estimation from human judgments, exploiting source, hypothesis, and reference information, with strong results on the WMT 2019 metrics evaluation.
- **Why it belongs:** Establishes the learned general-quality counterpart to our explicit term-retention measure.
- **What we should say:** "COMET learns MT quality prediction from human assessments using multilingual representations and source/reference information."
- **Boundary:** The framework paper does not specifically document the later `wmt22-comet-da` checkpoint or validate it on our chemical benchmark. Report the actual checkpoint separately.
- **Placement:** Paragraph 3; core evaluation background.

### 19. Zhang et al. (2020): BERTScore

**Citation:** Tianyi Zhang, Varsha Kishore, Felix Wu, Kilian Q. Weinberger, and Yoav Artzi. *BERTScore: Evaluating Text Generation with BERT*. ICLR 2020; initial preprint 2019. [Primary preprint record and paper](https://arxiv.org/abs/1904.09675).

- **Verified contribution:** Matches candidate/reference tokens using contextual embedding similarity rather than exact token identity; evaluates correlation with human judgments and robustness to paraphrases.
- **Why it belongs:** Explains the semantic-similarity diagnostic used alongside lexical scores and term coverage.
- **What we should say:** "BERTScore measures contextual token similarity, allowing comparison beyond exact reference wording."
- **Boundary:** Embedding-based precision/recall/F1 are not chemical-term precision/recall/F1. The paper does not establish chemical identity validation or validate our term-only concatenation diagnostic.
- **Placement:** Paragraph 3 or Evaluation.

### 20. Freitag et al. (2021): expert MQM evaluation

**Citation:** Markus Freitag, George Foster, David Grangier, Viresh Ratnakar, Qijun Tan, and Wolfgang Macherey. *Experts, Errors, and Context: A Large-Scale Study of Human Evaluation for Machine Translation*. TACL 9 (2021), 1460-1474. [Publication and PDF](https://aclanthology.org/2021.tacl-1.87/). DOI: 10.1162/tacl_a_00437.

- **Verified contribution:** Evaluates MT with professional translators, document context, and explicit MQM error analysis; finds substantially different system rankings from the corresponding crowd evaluation.
- **Why it belongs:** Motivates expert error analysis and cautions against equating our automatic MQM-style judge with professional assessment.
- **What we should say:** "Expert MQM evaluation demonstrates that annotator expertise, explicit error analysis, and document context can materially affect MT assessment."
- **Boundary:** Our segment-level LLM judge is not that human protocol, and its severity weights are not validated by citing this paper. Expert chemical assessment remains future work.
- **Placement:** Paragraph 3; closing evaluation qualification.

## One-page draft

The numbered citations refer to the 20 entries above and should be converted to the paper's bibliography keys during integration. This is proposed related-work prose, not a report of completed experiments.

Large language models have been studied as translation systems, with work examining their capabilities, prompting strategies, and adaptation. Hendy et al. compare GPT models with research and commercial MT systems across 18 directions, finding competitive high-resource performance alongside low-resource limitations in their setup [1]. Vilar et al. show that demonstration quality affects PaLM translation, while optimized prompting still trails supervised systems in their evaluation [4]. Moslem et al. investigate adaptation through in-domain examples and terminology [5]. These studies establish LLM translation as an active research area whose outcomes depend on language and conditioning.

Translation benchmarks provide the controlled comparisons needed to assess these capabilities. FLORES-101 offers professionally translated, fully aligned multilingual references for many-to-many evaluation [2]. WMT25 evaluates 60 submitted, LLM, and online-provider systems, emphasizing challenging source material and difficulty sampling [3]. Its human evaluation covers 15 of the 30 offered language pairs across four to five domains, using professional ESA or MQM assessment, with whole-document source context. These designs motivate comparisons on shared material while making language coverage, test difficulty, and context explicit; our segment-level evaluation does not reproduce WMT25's document-level protocol.

Comparing model performance requires complementary metrics. BLEU measures n-gram overlap [15], SacreBLEU standardizes reporting [16], and chrF++ combines character and word overlap [17]. COMET predicts quality from human judgments [18], whereas BERTScore measures contextual token similarity [19]. Expert MQM evaluation illustrates the importance of annotator expertise and document context [20]. Terminology accuracy adds a domain-sensitive dimension: the WMT terminology task establishes dedicated multilingual evaluation [7], while variation-aware work distinguishes legitimate renderings from undesirable inconsistency [9]. However, reference-term retention is narrower than source-conditioned terminology accuracy: matching a target span does not establish contextual correctness, and missing a reference form need not imply mistranslation. Our terminology metrics therefore complement, rather than replace, general translation assessment.

Terminology extraction supplies annotations for such diagnostics. Chun et al. use syntactically retrieved demonstrations to improve LLM term-boundary prediction on specialized benchmarks [10]. This motivates attention to extraction quality, but does not validate our pipeline; reference occurrence checks alone establish neither annotation completeness nor expert correctness.

In our target domain, chemical-patent prose must be distinguished from adjacent chemical NLP tasks. STOUT studies molecular representation-to-name conversion with structure-oriented checks [11], while CHEMDNER evaluates chemical mention recognition against expert annotations [12]; neither is multilingual prose translation. Legal translation provides a comparison domain through JRC-Acquis [13] and its OPUS distribution [14]. LegISTyr evaluates legal terminology injection and distinguishes insertion from contextual choice and fluency [6]; an EEA terminology suite reports performance that need not follow general MT rankings [8]. Building on this work, our study centers on multilingual chemical-patent translation capability, with legal comparison data and complementary terminology metrics. Source-only evaluation remains primary; reference-derived terminology hints form a separate oracle-assisted condition, not a deployable glossary baseline or evidence of unassisted capability.

## Integration cautions

- Lead the title, abstract, research questions, and main results with translation capability and benchmarking. Terminology metrics are a supporting contribution, not a substitute for overall translation evaluation.
- Frame the primary questions as: which systems translate specialized prose best; how capability varies across directions and domains; and what terminology diagnostics reveal beyond general scores. Do not assume the answers in advance.
- Keep source-only and oracle-assisted results in separate tables or clearly separated conditions. Use paired examples and fixed configurations for fair comparisons; document model versions, prompts, decoding settings, failures, and aggregation choices. Include dedicated MT comparators where feasible, or explicitly limit conclusions to the evaluated LLM roster.
- Report uncertainty and paired comparisons before asserting small ranking differences. Audit document/patent-family overlap, reference quality, and possible benchmark contamination; a provenance record alone does not establish independence or absence of training exposure.
- Do not claim the first terminology-sensitive MT benchmark, the first legal terminology-injection study, or that terminology prompting itself is new; papers 5-9 provide relevant prior work.
- Do not claim literature-wide absence of chemical prose translation studies from this targeted shortlist. Frame the contribution positively around the actual resource, annotation provenance, and controlled evaluation.
- Our coverage score measures retained target spans, not source-conditioned bilingual terminology accuracy. Extra hallucinated terms and contextual misuse require additional evaluation.
- Automatic extraction, external-database support, LLM curation, and expert validation are different statuses. Papers 10 and 12 are particularly useful when explaining this distinction; paper 2 also makes clear why corpus-derived references must not be described as newly professionally translated gold data.
- The current Methods section describes legal articles and excludes the separate definition snapshot. Decide whether definitions enter the experimental scope before describing them in the paper; selecting passages by definition markers does not make them isolated gold definitions.
- Cite the actual patent dataset artifact separately in Data. It is not counted as a research paper here. IATE, Wikidata, AGROVOC, UNTERM, and extractor model cards also need resource attribution, but should not be used to inflate the 20-paper list.
- Preserve the oracle label in the abstract, experimental conditions, tables, and conclusions. Do not report the assisted condition as a realistic source-only translation baseline.
- Do not assert benchmark gains, model rankings, improved extraction accuracy, or chemical validity until the corresponding experiments and validation are complete.

## Research note

Discovery used targeted ACL Anthology searches for terminology-aware LLM translation, terminology evaluation, adaptive MT, and JRC-Acquis, followed by primary publication pages; chemistry records were cross-checked with Europe PMC by DOI and accessible full text. The translation-first revision additionally checked primary abstracts and metadata for Hendy et al. and FLORES-101. The current narrative replaces WMT24 with the WMT25 General MT findings, verified from its official ACL publication record and abstract, not from the unrelated first paper in the WMT25 proceedings. The shortlist retains exactly 20 papers and includes established foundations and recent 2025-2026 comparators. It supports a concise synthesis, not comprehensive coverage of every patent-MT system, every metric, or chemical NLP. Domain-specific prose-translation comparators and any stronger novelty claim still require a broader search and full-text comparison.