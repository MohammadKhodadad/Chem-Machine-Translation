from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from dataclasses import asdict
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import torch
from comet import load_from_checkpoint
from huggingface_hub import snapshot_download

from chem_machine_translation.evaluation.aligned_comet import (
    AlignedCometConfig,
    AlignedCometScorer,
    SentAlignCometConfig,
    SentAlignCometScorer,
    TokenCheckedCometScorer,
    TransformersSentenceEmbedder,
)
from chem_machine_translation.evaluation.metrics import UnbabelCometScorer

PREFIX = [
    (
        "The laboratory documents each delivery before the containers enter the storage room.",
        "Das Labor dokumentiert jede Lieferung, bevor die Behaelter den Lagerraum erreichen.",
    ),
    (
        "The staff check the labels and record the batch number in the register.",
        "Die Mitarbeiter pruefen die Etiketten und erfassen die Chargennummer im Register.",
    ),
    (
        "Each sample receives a unique identifier that remains visible during the examination.",
        "Jede Probe erhaelt eine eindeutige Kennung, "
        "die waehrend der Untersuchung sichtbar bleibt.",
    ),
    (
        "The analyst checks the instrument before measuring the composition of the solution.",
        "Der Analyst prueft das Instrument, bevor er die Zusammensetzung der Loesung misst.",
    ),
    (
        "The supervisor reviews the written report and signs the completed inspection record.",
        "Der Vorgesetzte prueft den schriftlichen Bericht "
        "und unterschreibt das fertige Pruefprotokoll.",
    ),
    (
        "The records describe the procedure "
        "and identify the employee responsible for each operation.",
        "Die Unterlagen beschreiben das Verfahren "
        "und nennen den fuer jeden Vorgang verantwortlichen Mitarbeiter.",
    ),
]
CORRECT_TAIL = [
    (
        "The waste must be collected in sealed containers "
        "and sent to an approved disposal facility.",
        "Der Abfall muss in verschlossenen Behaeltern gesammelt "
        "und zu einer zugelassenen Entsorgungsanlage gebracht werden.",
        "Der Abfall darf in offenen Behaeltern bleiben und ohne Genehmigung in den Fluss gelangen.",
    ),
    (
        "Workers must wear protective gloves and safety glasses "
        "when handling the concentrated solution.",
        "Die Arbeiter muessen beim Umgang mit der konzentrierten Loesung "
        "Schutzhandschuhe und Schutzbrillen tragen.",
        "Die Arbeiter duerfen beim Umgang mit der konzentrierten Loesung "
        "keine Schutzhandschuhe oder Schutzbrillen tragen.",
    ),
    (
        "The valve must remain closed until the pressure falls below the specified safety limit.",
        "Das Ventil muss geschlossen bleiben, "
        "bis der Druck unter die festgelegte Sicherheitsgrenze sinkt.",
        "Das Ventil muss geoeffnet bleiben, "
        "solange der Druck ueber der festgelegten Sicherheitsgrenze liegt.",
    ),
    (
        "The manufacturer must notify the authority immediately "
        "if a batch contains prohibited impurities.",
        "Der Hersteller muss die Behoerde unverzueglich informieren, "
        "wenn eine Charge verbotene Verunreinigungen enthaelt.",
        "Der Hersteller darf die Behoerde nicht informieren, "
        "wenn eine Charge verbotene Verunreinigungen enthaelt.",
    ),
    (
        "The permit expires after twelve months and must be renewed before production continues.",
        "Die Genehmigung endet nach zwoelf Monaten "
        "und muss vor der Fortsetzung der Produktion erneuert werden.",
        "Die Genehmigung gilt unbegrenzt "
        "und muss vor der Fortsetzung der Produktion niemals erneuert werden.",
    ),
    (
        "The finished product must not be released "
        "until the independent quality inspection is complete.",
        "Das fertige Produkt darf erst freigegeben werden, "
        "wenn die unabhaengige Qualitaetspruefung abgeschlossen ist.",
        "Das fertige Produkt muss vor der unabhaengigen Qualitaetspruefung freigegeben werden.",
    ),
]
UNRELATED_TAIL = [
    "Die Fussballmannschaft reist am Samstag zu einem Turnier in einer anderen Stadt.",
    "Im Theater beginnt eine neue Komoedie mit Musik und bunten Kostuemen.",
    "Die Familie verbringt ihren Urlaub am Strand und besucht jeden Morgen den Markt.",
    "Ein Musiker spielt auf der Gitarre, waehrend die Besucher im Garten tanzen.",
    "Die Baeckerei verkauft frisches Brot und suesses Gebaeck fuer das gemeinsame Fruehstueck.",
    "Die Kinder malen Bilder von Tieren und bauen eine Burg aus Sand.",
]

MULTILINGUAL_TEXTS = {
    "es": {
        "prefix": [
            "El laboratorio documenta cada entrega "
            "antes de que los recipientes entren en el almacén.",
            "El personal comprueba las etiquetas y registra el número de lote en el registro.",
            "Cada muestra recibe un identificador único que permanece visible durante el examen.",
        ],
        "tail": [
            "Los residuos deben recogerse en recipientes sellados "
            "y enviarse a una instalación de eliminación autorizada.",
            "Los trabajadores deben usar guantes y gafas de protección "
            "al manipular la solución concentrada.",
            "La válvula debe permanecer cerrada hasta que la presión caiga "
            "por debajo del límite de seguridad especificado.",
        ],
        "contradiction": [
            "Los residuos pueden permanecer en recipientes abiertos "
            "y verterse al río sin autorización.",
            "Los trabajadores no deben usar guantes ni gafas de protección "
            "al manipular la solución concentrada.",
            "La válvula debe permanecer abierta mientras la presión supere "
            "el límite de seguridad especificado.",
        ],
        "unrelated": [
            "El equipo de fútbol viaja el sábado a un torneo en otra ciudad.",
            "Una nueva comedia con música y trajes coloridos comienza en el teatro.",
            "La familia pasa sus vacaciones en la playa y visita el mercado cada mañana.",
        ],
    },
    "fr": {
        "prefix": [
            "Le laboratoire documente chaque livraison "
            "avant que les récipients entrent dans le local de stockage.",
            "Le personnel vérifie les étiquettes et inscrit le numéro de lot dans le registre.",
            "Chaque échantillon reçoit un identifiant unique qui reste visible pendant l'examen.",
        ],
        "tail": [
            "Les déchets doivent être collectés dans des récipients scellés "
            "et envoyés dans une installation d'élimination agréée.",
            "Les travailleurs doivent porter des gants et des lunettes de protection "
            "lors de la manipulation de la solution concentrée.",
            "La vanne doit rester fermée jusqu'à ce que la pression tombe "
            "sous la limite de sécurité spécifiée.",
        ],
        "contradiction": [
            "Les déchets peuvent rester dans des récipients ouverts "
            "et être rejetés dans la rivière sans autorisation.",
            "Les travailleurs ne doivent porter ni gants ni lunettes de protection "
            "lors de la manipulation de la solution concentrée.",
            "La vanne doit rester ouverte tant que la pression dépasse "
            "la limite de sécurité spécifiée.",
        ],
        "unrelated": [
            "L'équipe de football se rend samedi à un tournoi dans une autre ville.",
            "Une nouvelle comédie avec de la musique et des costumes colorés commence au théâtre.",
            "La famille passe ses vacances à la plage et visite le marché chaque matin.",
        ],
    },
    "pt": {
        "prefix": [
            "O laboratório documenta cada entrega "
            "antes de os recipientes entrarem na sala de armazenamento.",
            "Os funcionários verificam os rótulos e registam o número do lote no registo.",
            "Cada amostra recebe um identificador único que permanece visível durante o exame.",
        ],
        "tail": [
            "Os resíduos devem ser recolhidos em recipientes selados "
            "e enviados para uma instalação de eliminação autorizada.",
            "Os trabalhadores devem usar luvas e óculos de proteção "
            "ao manusear a solução concentrada.",
            "A válvula deve permanecer fechada até que a pressão desça "
            "abaixo do limite de segurança especificado.",
        ],
        "contradiction": [
            "Os resíduos podem permanecer em recipientes abertos "
            "e ser despejados no rio sem autorização.",
            "Os trabalhadores não devem usar luvas nem óculos de proteção "
            "ao manusear a solução concentrada.",
            "A válvula deve permanecer aberta enquanto a pressão estiver "
            "acima do limite de segurança especificado.",
        ],
        "unrelated": [
            "A equipa de futebol viaja no sábado para um torneio noutra cidade.",
            "Uma nova comédia com música e trajes coloridos começa no teatro.",
            "A família passa as férias na praia e visita o mercado todas as manhãs.",
        ],
    },
    "ru": {
        "prefix": [
            "Лаборатория документирует каждую поставку "
            "до поступления контейнеров в складское помещение.",
            "Сотрудники проверяют этикетки и записывают номер партии в журнал.",
            "Каждый образец получает уникальный идентификатор, "
            "который остаётся видимым во время исследования.",
        ],
        "tail": [
            "Отходы необходимо собирать в герметичные контейнеры "
            "и отправлять на утверждённое предприятие по утилизации.",
            "При работе с концентрированным раствором работники "
            "должны носить защитные перчатки и очки.",
            "Клапан должен оставаться закрытым, "
            "пока давление не упадёт ниже установленного безопасного предела.",
        ],
        "contradiction": [
            "Отходы можно оставлять в открытых контейнерах и сбрасывать в реку без разрешения.",
            "При работе с концентрированным раствором работники "
            "не должны носить защитные перчатки и очки.",
            "Клапан должен оставаться открытым, "
            "пока давление превышает установленный безопасный предел.",
        ],
        "unrelated": [
            "Футбольная команда в субботу отправляется на турнир в другой город.",
            "В театре начинается новая комедия с музыкой и яркими костюмами.",
            "Семья проводит отпуск на пляже и каждое утро посещает рынок.",
        ],
    },
    "zh": {
        "prefix": [
            "在容器进入储藏室之前，实验室会记录每一批交付的物品。",
            "工作人员检查标签，并在登记簿中记录批次编号。",
            "每个样品都获得一个唯一标识符，该标识符在检验期间始终保持可见。",
        ],
        "tail": [
            "废物必须收集在密封容器中，并送往经批准的废物处理设施。",
            "处理浓缩溶液时，工作人员必须佩戴防护手套和护目镜。",
            "在压力降至规定的安全限值以下之前，阀门必须保持关闭。",
        ],
        "contradiction": [
            "废物可以留在敞开的容器中，并在未经批准的情况下排入河流。",
            "处理浓缩溶液时，工作人员不得佩戴防护手套和护目镜。",
            "只要压力超过规定的安全限值，阀门就必须保持打开。",
        ],
        "unrelated": [
            "足球队将在星期六前往另一座城市参加比赛。",
            "剧院开始上演一部配有音乐和鲜艳服装的新喜剧。",
            "一家人在海滩度假，每天早晨都会去市场。",
        ],
    },
    "ja": {
        "prefix": [
            "容器が保管室に入る前に、研究所はすべての納品を記録します。",
            "職員はラベルを確認し、登録簿にロット番号を記録します。",
            "各試料には固有の識別番号が付けられ、検査中もその番号が見える状態に保たれます。",
        ],
        "tail": [
            "廃棄物は密閉容器に集め、認可された廃棄物処理施設に送らなければなりません。",
            "濃縮溶液を扱う作業員は、保護手袋と保護眼鏡を着用しなければなりません。",
            "圧力が指定された安全限界を下回るまで、弁は閉じたままにしなければなりません。",
        ],
        "contradiction": [
            "廃棄物は開いた容器に残し、許可なく川に流してもかまいません。",
            "濃縮溶液を扱う作業員は、保護手袋と保護眼鏡を着用してはなりません。",
            "圧力が指定された安全限界を超えている間、弁は開いたままにしなければなりません。",
        ],
        "unrelated": [
            "サッカーチームは土曜日に別の都市で開催される大会へ出発します。",
            "劇場では音楽と色鮮やかな衣装を使った新しい喜劇が始まります。",
            "家族は海辺で休暇を過ごし、毎朝市場を訪れます。",
        ],
    },
}


def multilingual_cases(tokenizer):
    texts_by_language = {
        "en": {
            "prefix": [entry[0] for entry in PREFIX[:3]],
            "tail": [entry[0] for entry in CORRECT_TAIL[:3]],
            "contradiction": [
                "The waste may remain in open containers "
                "and be discharged into the river without approval.",
                "Workers must not wear protective gloves or safety glasses "
                "when handling the concentrated solution.",
                "The valve must remain open while the pressure exceeds the specified safety limit.",
            ],
            "unrelated": [
                "The football team travels on Saturday to a tournament in another city.",
                "A new comedy with music and colourful costumes starts at the theatre.",
                "The family spends its holiday at the beach and visits the market every morning.",
            ],
        },
        "de": {
            "prefix": [entry[1] for entry in PREFIX[:3]],
            "tail": [entry[1] for entry in CORRECT_TAIL[:3]],
            "contradiction": [entry[2] for entry in CORRECT_TAIL[:3]],
            "unrelated": UNRELATED_TAIL[:3],
        },
        **MULTILINGUAL_TEXTS,
    }
    cases = []
    for language, texts in texts_by_language.items():
        source_language = "de" if language == "en" else "en"
        source_texts = texts_by_language[source_language]
        target_prefix, source_prefix = [], []
        while True:
            index = len(target_prefix) % 3
            proposed = target_prefix + [texts["prefix"][index]]
            count = len(tokenizer.encode("\n".join(proposed), add_special_tokens=False))
            if count > 500:
                break
            target_prefix = proposed
            source_prefix.append(source_texts["prefix"][index])
            if count >= 475:
                break
        repetitions = 1
        while len(tokenizer.encode(
            "\n".join(target_prefix + texts["tail"] * repetitions),
            add_special_tokens=True,
        )) <= 1000:
            repetitions += 1
        for corruption in ("control", "unrelated", "contradiction"):
            target_tail = texts["tail" if corruption == "control" else corruption]
            cases.append({
                "name": f"{source_language}_{language}_{corruption}",
                "source_language": source_language, "target_language": language,
                "corruption": corruption,
                "source": "\n".join(source_prefix + source_texts["tail"] * repetitions),
                "reference": "\n".join(target_prefix + texts["tail"] * repetitions),
                "prediction": "\n".join(target_prefix + target_tail * repetitions),
                "shared_prefix": "\n".join(target_prefix),
                "prefix_content_tokens": len(tokenizer.encode(
                    "\n".join(target_prefix), add_special_tokens=False,
                )),
            })
    return cases


class CachedEmbedder(TransformersSentenceEmbedder):
    def __init__(self, config):
        super().__init__(config)
        self.cache = {}

    def encode(self, texts):
        missing = list(dict.fromkeys(text for text in texts if text not in self.cache))
        if missing:
            self.cache.update(zip(missing, super().encode(missing), strict=True))
        return [self.cache[text] for text in texts]


class CachedComet(TokenCheckedCometScorer):
    def __init__(self, model):
        super().__init__(batch_size=8)
        self._model = model
        self.cache = {}

    def score_many(self, blocks):
        keys = [(block["source"], block["reference"], block["prediction"]) for block in blocks]
        missing = list(dict.fromkeys(key for key in keys if key not in self.cache))
        if missing:
            payload = [{"source": key[0], "reference": key[1], "prediction": key[2]}
                       for key in missing]
            self.cache.update(zip(missing, super().score_many(payload), strict=True))
        return [self.cache[key] for key in keys]


def build_case(tokenizer, name, prefix_target, corruption):
    source_prefix, target_prefix = [], []
    while len(tokenizer.encode(" ".join(target_prefix), add_special_tokens=False)) < prefix_target:
        source_sentence, target_sentence = PREFIX[len(target_prefix) % len(PREFIX)]
        proposed = " ".join(target_prefix + [target_sentence])
        if len(tokenizer.encode(proposed, add_special_tokens=False)) > 500:
            break
        source_prefix.append(source_sentence)
        target_prefix.append(target_sentence)
    source_tail = [entry[0] for entry in CORRECT_TAIL] * 4
    reference_tail = [entry[1] for entry in CORRECT_TAIL] * 4
    prediction_tail = (
        reference_tail if corruption == "control" else
        UNRELATED_TAIL * 4 if corruption == "unrelated" else
        [entry[2] for entry in CORRECT_TAIL] * 4
    )
    return {
        "name": name, "corruption": corruption,
        "source": " ".join(source_prefix + source_tail),
        "reference": " ".join(target_prefix + reference_tail),
        "prediction": " ".join(target_prefix + prediction_tail),
        "shared_prefix": " ".join(target_prefix),
        "prefix_content_tokens": len(
            tokenizer.encode(" ".join(target_prefix), add_special_tokens=False)
        ),
    }


def first_difference(left, right):
    for index, (left_token, right_token) in enumerate(zip(left, right, strict=False)):
        if left_token != right_token:
            return index
    return min(len(left), len(right)) if len(left) != len(right) else None


def structural_cases():
    sources, references = zip(*PREFIX[:3], strict=True)
    split_words = references[1].split()
    split_point = len(split_words) // 2
    candidates = {
        "control": list(references),
        "split": [references[0], " ".join(split_words[:split_point]),
                  " ".join(split_words[split_point:]), references[2]],
        "merge": [references[0].removesuffix(".") + " " + references[1], references[2]],
        "omission": [references[0], references[2]],
        "addition": [*references, UNRELATED_TAIL[0]],
        "duplication": [references[0], references[1], references[1], references[2]],
        "reordering": [references[1], references[0], references[2]],
    }
    return [{
        "name": f"structural_en_de_{condition}", "source_language": "en",
        "target_language": "de", "corruption": condition,
        "suite": "short_structural", "source": "\n".join(sources),
        "reference": "\n".join(references), "prediction": "\n".join(candidate),
        "shared_prefix": "", "prefix_content_tokens": 0,
    } for condition, candidate in candidates.items()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/aligned_comet_long_prefix/bge_multilingual_results.json"),
    )
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--compare-three", action="store_true")
    parser.add_argument("--exclude-overlong-blocks", action="store_true")
    args = parser.parse_args()
    if args.list_cases:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-large", local_files_only=True)
        cases = multilingual_cases(tokenizer)
        assert len(cases) == 24
        assert {case["target_language"] for case in cases} == {
            "en", "de", "es", "fr", "pt", "ru", "zh", "ja",
        }
        assert all(400 <= case["prefix_content_tokens"] <= 500 for case in cases)
        for case in cases:
            print(case["name"], case["prefix_content_tokens"])
        if args.compare_three:
            for case in structural_cases():
                assert case["source"] and case["reference"] and case["prediction"]
                print(case["name"], case["suite"])
        return
    if args.compare_three:
        if args.output == Path("reports/aligned_comet_long_prefix/bge_multilingual_results.json"):
            args.output = Path("reports/aligned_comet_long_prefix/three_metric_comparison.json")
        if args.output.exists():
            raise FileExistsError(f"Choose a new comparison output; preserving {args.output}")
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    checkpoint_dir = Path(snapshot_download("Unbabel/wmt22-comet-da", local_files_only=True))
    checkpoints = sorted(checkpoint_dir.rglob("*.ckpt"))
    if not checkpoints:
        raise RuntimeError("No complete COMET checkpoint is cached.")
    print("Loading cached COMET checkpoint...", flush=True)
    model = load_from_checkpoint(str(checkpoints[0]))
    model.eval()
    tokenizer = model.encoder.tokenizer
    embedding_path = snapshot_download("BAAI/bge-m3", local_files_only=True)
    config = AlignedCometConfig(
        embedding_model=embedding_path, exclude_overlong_blocks=args.exclude_overlong_blocks,
    )
    aligned = AlignedCometScorer(
        config=config, embedder=CachedEmbedder(config), comet_scorer=CachedComet(model),
    )
    regular = UnbabelCometScorer(batch_size=8)
    regular._model = model
    sentalign = None
    if args.compare_three:
        sentalign = SentAlignCometScorer(
            SentAlignCometConfig(
                alignment_model=embedding_path,
                alignment_cache=str(Path("benchmark_work/sentalign_embedding_cache").resolve()),
                exclude_overlong_blocks=args.exclude_overlong_blocks,
            ),
            comet_scorer=CachedComet(model),
        )
    cases = [
        build_case(tokenizer, "prefix_450_control", 450, "control"),
        build_case(tokenizer, "prefix_450_unrelated", 450, "unrelated"),
        build_case(tokenizer, "prefix_500_control", 500, "control"),
        build_case(tokenizer, "prefix_500_unrelated", 500, "unrelated"),
        build_case(tokenizer, "prefix_500_contradiction", 500, "contradiction"),
        build_case(tokenizer, "prefix_450_contradiction", 450, "contradiction"),
    ] + multilingual_cases(tokenizer)
    if args.compare_three:
        cases += structural_cases()
    results = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        print(
            f"Scoring {case['name']} (prefix {case['prefix_content_tokens']} tokens)...",
            flush=True,
        )
        token_ids = {field: tokenizer.encode(case[field], add_special_tokens=True, truncation=False)
                     for field in ("source", "reference", "prediction")}
        retained = {field: model.encoder.prepare_sample([case[field]])["input_ids"][0].tolist()
                    for field in token_ids}
        if case.get("suite") != "short_structural":
            assert 400 <= case["prefix_content_tokens"] <= 500
            assert len(token_ids["reference"]) > 900
        assert all(len(tokens) <= 510 for tokens in retained.values())
        old_score = regular.score(case["source"], case["prediction"], case["reference"])
        new_result = aligned.score_document(
            source=case["source"], prediction=case["prediction"], reference=case["reference"],
            source_language=case.get("source_language", "en"),
            target_language=case.get("target_language", "de"),
        )
        row = {
            **case, "regular_comet": old_score, "aligned_comet": new_result.score,
            "null_alignment_ratio": new_result.null_alignment_ratio,
            "block_states": dict(Counter(block["state"] for block in new_result.blocks)),
            "full_token_counts": {field: len(tokens) for field, tokens in token_ids.items()},
            "regular_retained_token_counts": {
                field: len(tokens) for field, tokens in retained.items()
            },
            "first_different_token": first_difference(
                token_ids["reference"], token_ids["prediction"]
            ),
            "regular_reference_prediction_ids_equal": (
                retained["reference"] == retained["prediction"]
            ),
            "aligned_details": asdict(new_result),
        }
        if sentalign is not None:
            row["comet"] = old_score
            row["reference_assignment_comet"] = new_result.score
            try:
                sentalign_result = sentalign.score_document(
                    source=case["source"], prediction=case["prediction"],
                    reference=case["reference"],
                    source_language=case.get("source_language", "en"),
                    target_language=case.get("target_language", "de"),
                )
                row["sentalign_comet"] = sentalign_result.score
                row["sentalign_details"] = asdict(sentalign_result)
            except (ValueError, RuntimeError) as exc:
                row["sentalign_comet"] = None
                row["sentalign_error"] = str(exc)
        results.append(row)
        report = {
            "protocol": (
                "Synthetic multilingual shared-prefix stress test; not a benchmark validation."
            ),
            "embedding_model": "BAAI/bge-m3",
            "embedding_snapshot": embedding_path, "comet_checkpoint": str(checkpoints[0]),
            "config": asdict(config), "results": results,
        }
        if sentalign is not None:
            report["sentalign_config"] = asdict(sentalign.config)
            report["comparison"] = (
                "Ordinary COMET vs reference_assignment_comet vs sentalign_comet; "
                "30 long-prefix cases plus 7 short structural cases. "
                "Both aligners use BGE-M3 with CLS pooling. "
                "Alignment and resulting aggregation blocks differ. "
                "SentAlign cutoff 0.4 is retained without BGE-specific tuning."
            )
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        print(json.dumps({key: row[key] for key in (
            "name", "prefix_content_tokens", "regular_comet", "aligned_comet",
            "null_alignment_ratio", "block_states", "full_token_counts", "first_different_token",
        )}), flush=True)
        if sentalign is not None:
            print(json.dumps({key: row[key] for key in (
                "name", "comet", "reference_assignment_comet", "sentalign_comet",
            )} | {"sentalign_error": row.get("sentalign_error")}), flush=True)
    controls = {
        (row.get("target_language", "de"), row["prefix_content_tokens"]): row
        for row in results if row["corruption"] == "control"
    }
    for row in results:
        control = controls[(row.get("target_language", "de"), row["prefix_content_tokens"])]
        row["regular_drop_from_control"] = control["regular_comet"] - row["regular_comet"]
        row["aligned_drop_from_control"] = (
            control["aligned_comet"] - row["aligned_comet"]
            if control["aligned_comet"] is not None and row["aligned_comet"] is not None else None
        )
        if sentalign is not None:
            row["sentalign_drop_from_control"] = (
                control["sentalign_comet"] - row["sentalign_comet"]
                if control["sentalign_comet"] is not None and row["sentalign_comet"] is not None
                else None
            )
    report["results"] = results
    if sentalign is not None:
        report["summary"] = []
        for suite in ("long_prefix", "short_structural"):
            suite_rows = [row for row in results if row.get("suite", "long_prefix") == suite]
            for condition in sorted({row["corruption"] for row in suite_rows}):
                rows = [row for row in suite_rows if row["corruption"] == condition]
                for metric in ("comet", "reference_assignment_comet", "sentalign_comet"):
                    values = [row[metric] for row in rows
                              if row[metric] is not None and math.isfinite(row[metric])]
                    report["summary"].append({
                        "suite": suite, "condition": condition, "metric": metric,
                        "case_count": len(rows), "scored_count": len(values),
                        "mean": sum(values) / len(values) if values else None,
                    })
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(
        f"Saved all {len(results)} cases and full text/segment audits to {args.output}", flush=True
    )


if __name__ == "__main__":
    main()