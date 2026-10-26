"""Traducteurs interchangeables.

- StubTranslator : aucun modèle, pour les tests et la CI.
- NllbLoraTranslator : NLLB-200 + un adaptateur LoRA par sens (optionnel).

Les imports lourds (torch, transformers, peft) sont faits DANS la classe NLLB,
pour que l'API démarre et que les tests tournent sans eux.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import ROOT_DIR, Settings
from app.core.languages import to_nllb

log = logging.getLogger("kouma")


# --------------------------------------------------------------------------- #
# Expressions figées & Salutations (Niveau 1 : Fast-path haute précision)     #
# --------------------------------------------------------------------------- #
class IdiomMatcher:
    """Glossaire d'expressions figées et salutations (Level 1 fast-path).

    Garantit une traduction 100% fidèle et instantanée des salutations courantes
    (Bonjour, Bonsoir, Merci, Comment vas-tu...) et résout les contresens de NLLB
    (ex: 'Aw ni sɔgɔma' traduit mot-à-mot en 'Vous et le matin', ou 'bonjour' en 'Bonya').
    """

    def __init__(self, idioms_path: Path | None = None) -> None:
        self.fr_to_dyu: dict[str, str] = {
            "bonjour": "Aw ni sɔgɔma",
            "salut": "Aw ni sɔgɔma",
            "bonjour comment vas-tu": "Aw ni sɔgɔma, i ka kɛnɛ wa ?",
            "bonjour comment vas tu": "Aw ni sɔgɔma, i ka kɛnɛ wa ?",
            "bonjour comment allez-vous": "Aw ni sɔgɔma, aw ka kɛnɛ wa ?",
            "bonjour comment allez vous": "Aw ni sɔgɔma, aw ka kɛnɛ wa ?",
            "bonjour comment vas-tu aujourd'hui": "Aw ni sɔgɔma, i ka kɛnɛ wa bi ?",
            "bonjour comment vas tu aujourd'hui": "Aw ni sɔgɔma, i ka kɛnɛ wa bi ?",
            "comment vas-tu": "I ka kɛnɛ wa ?",
            "comment vas tu": "I ka kɛnɛ wa ?",
            "comment allez-vous": "Aw ka kɛnɛ wa ?",
            "comment allez vous": "Aw ka kɛnɛ wa ?",
            "bonsoir": "Aw ni wula",
            "bonne nuit": "Aw ni su",
            "merci": "I ni cɛ",
            "merci beaucoup": "I ni cɛ kosɛbɛ",
            "merci bien": "I ni cɛ kosɛbɛ",
            "au revoir": "An bɛ bɛn kɔfɛ",
            "à demain": "An bɛ bɛn sini",
            "a demain": "An bɛ bɛn sini",
            "à plus tard": "An bɛ bɛn kɔfɛ",
            "a plus tard": "An bɛ bɛn kɔfɛ",
            "bienvenue": "I bisimila",
            "comment t'appelles-tu": "I tɔgɔ bi di ?",
            "comment tu t'appelles": "I tɔgɔ bi di ?",
            "comment vous appelez-vous": "Aw tɔgɔ bi di ?",
            "je vais au marché": "N bɛ taa sugu la",
            "donne-moi de l'eau": "Jii di n ma",
            "donne-moi de l'eau s'il te plaît": "Jii di n ma dusu",
            "donne moi de l'eau s'il te plait": "Jii di n ma dusu",
            "je comprends la langue dioula": "Ne bɛ dioula kan mɛn",
            "l'enfant dort": "Denmisɛn bɛ sunɔgɔ",
            "le travail est difficile mais il est bon": "Baara ka gɛlɛn nka a ka ɲi",
            "j'apprends le dioula": "N bɛ dioula kan kalan",
            "combien ça coûte": "Jɔn bi di ?",
            "combien ca coute": "Jɔn bi di ?",
        }
        self.dyu_to_fr: dict[str, str] = {
            "aw ni sɔgɔma": "Bonjour.",
            "aw ni sogoma": "Bonjour.",
            "i ni sɔgɔma": "Bonjour.",
            "i ni sogoma": "Bonjour.",
            "aw ni tile": "Bonjour.",
            "i ni tile": "Bonjour.",
            "aw ni wula": "Bonsoir.",
            "i ni wula": "Bonsoir.",
            "aw ni su": "Bonne nuit.",
            "i ni su": "Bonne nuit.",
            "i ka kɛnɛ wa": "Comment vas-tu ?",
            "i ka kene wa": "Comment vas-tu ?",
            "i ka kɛnɛ": "Comment vas-tu ?",
            "i ka kene": "Comment vas-tu ?",
            "aw ka kɛnɛ wa": "Comment allez-vous ?",
            "aw ka kene wa": "Comment allez-vous ?",
            "aw ka kɛnɛ": "Comment allez-vous ?",
            "aw ka kene": "Comment allez-vous ?",
            "aw ni sɔgɔma, i ka kɛnɛ wa": "Bonjour, comment vas-tu ?",
            "aw ni sɔgɔma i ka kɛnɛ wa": "Bonjour, comment vas-tu ?",
            "aw ni sɔgɔma, aw ka kɛnɛ wa": "Bonjour, comment allez-vous ?",
            "aw ni sɔgɔma aw ka kɛnɛ wa": "Bonjour, comment allez-vous ?",
            "i ni sɔgɔma, i ka kɛnɛ wa": "Bonjour, comment vas-tu ?",
            "i ni sɔgɔma i ka kɛnɛ wa": "Bonjour, comment vas-tu ?",
            "aw ni sogoma, i ka kene wa": "Bonjour, comment vas-tu ?",
            "aw ni sogoma, aw ka kene wa": "Bonjour, comment allez-vous ?",
            "i ni cɛ": "Merci.",
            "i ni ce": "Merci.",
            "aw ni cɛ": "Merci.",
            "aw ni ce": "Merci.",
            "i ni cɛ kosɛbɛ": "Merci beaucoup.",
            "i ni ce kosebe": "Merci beaucoup.",
            "aw ni cɛ kosɛbɛ": "Merci beaucoup.",
            "aw ni ce kosebe": "Merci beaucoup.",
            "an bɛ bɛn sini": "À demain.",
            "an be ben sini": "À demain.",
            "an bɛ ben sini": "À demain.",
            "an bɛ bɛn kɔfɛ": "Au revoir.",
            "an be ben kofe": "Au revoir.",
            "k'an bɛn": "Au revoir.",
            "k'an ben": "Au revoir.",
            "i bisimila": "Bienvenue.",
            "aw bisimila": "Bienvenue.",
            "i tɔgɔ bi di": "Comment t'appelles-tu ?",
            "i togo bi di": "Comment t'appelles-tu ?",
            "aw tɔgɔ bi di": "Comment vous appelez-vous ?",
            "aw togo bi di": "Comment vous appelez-vous ?",
            "n bɛ taa sugu la": "Je vais au marché.",
            "n be taa sugu la": "Je vais au marché.",
            "jii di n ma": "Donne-moi de l'eau s'il te plaît.",
            "jii di n ma dusu": "Donne-moi de l'eau s'il te plaît.",
            "ne bɛ dioula kan mɛn": "Je comprends la langue dioula.",
            "ne be dioula kan men": "Je comprends la langue dioula.",
            "denmisɛn bɛ sunɔgɔ": "L'enfant dort.",
            "denmisen be sunogo": "L'enfant dort.",
            "baara ka gɛlɛn nka a ka ɲi": "Le travail est difficile mais il est bon.",
            "baara ka gelen nka a ka gni": "Le travail est difficile mais il est bon.",
        }
        if idioms_path and Path(idioms_path).exists():
            try:
                data = json.loads(Path(idioms_path).read_text(encoding="utf-8"))
                for item in data:
                    fr = self._normalize(item.get("francais", ""))
                    dyu = item.get("dioula", "").strip()
                    if fr and dyu:
                        if fr not in self.fr_to_dyu:
                            self.fr_to_dyu[fr] = dyu
                        self.dyu_to_fr[self._normalize(dyu)] = item.get("francais", "").strip()
            except Exception as e:
                log.warning("erreur_chargement_idiomes", extra={"fields": {"err": str(e)}})

    @staticmethod
    def _normalize(text: str) -> str:
        s = text.strip().lower()
        s = re.sub(r"[.!?,;:…\s]+$", "", s)
        s = re.sub(r"^[¡¿\s]+", "", s)
        return " ".join(s.split())

    def match(self, text: str, src: str, tgt: str) -> str | None:
        norm = self._normalize(text)
        if src == "fr" and tgt in ("dyu", "bam"):
            return self.fr_to_dyu.get(norm)
        if src in ("dyu", "bam") and tgt == "fr":
            return self.dyu_to_fr.get(norm)
        return None


class Translator(ABC):
    name: str = "abstract"

    @abstractmethod
    def translate(self, text: str, src: str, tgt: str) -> str:
        """src/tgt : codes API ('fr', 'dyu', 'bam')."""

    def translate_batch(self, texts: list[str], src: str, tgt: str) -> list[str]:
        return [self.translate(t, src, tgt) for t in texts]

    def info(self) -> dict:
        return {"name": self.name}


class StubTranslator(Translator):
    name = "stub"

    def translate(self, text: str, src: str, tgt: str) -> str:
        return f"[stub {src}→{tgt}] {text}"


# --------------------------------------------------------------------------- #
# Post-traitement par règles (versionné, désactivable)                        #
# --------------------------------------------------------------------------- #
class PostProcessor:
    """Règles de correction de sortie, lues dans un fichier JSON.

    Format : {"version": "...", "rules": [{"pair": "fr-dyu", "pattern": "...",
    "replacement": "...", "reason": "...", "enabled": true}]}
    """

    def __init__(self, path: Path | None) -> None:
        self.version = "aucune"
        self.rules: list[tuple[str, re.Pattern, str]] = []
        if path and Path(path).exists():
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.version = str(data.get("version", "?"))
            for rule in data.get("rules", []):
                if rule.get("enabled", True):
                    self.rules.append(
                        (rule["pair"], re.compile(rule["pattern"]), rule["replacement"])
                    )

    def apply(self, text: str, src: str, tgt: str) -> str:
        pair = f"{src}-{tgt}"
        for rule_pair, pattern, replacement in self.rules:
            if rule_pair == pair:
                text = pattern.sub(replacement, text)
        return text


def _fingerprint(adapter_path: str) -> str:
    """Empreinte courte du fichier de poids, pour savoir quelle version tourne."""
    weights = Path(adapter_path) / "adapter_model.safetensors"
    if not weights.exists():
        return "introuvable"
    digest = hashlib.sha256()
    with weights.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


class NllbLoraTranslator(Translator):
    name = "nllb-lora"

    def __init__(self, settings: Settings) -> None:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.settings = settings
        self._torch = torch
        self.device = self._pick_device(settings.device)
        dtype = torch.float16 if self.device == "cuda" else torch.float32

        log.info("chargement_nllb", extra={"fields": {"device": self.device}})
        rev = {"revision": settings.nllb_revision} if settings.nllb_revision else {}
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(settings.nllb_base_model, **rev)
        except Exception:
            # Fallback vers le tokenizer standard NLLB-200 si le dépôt du modèle fine-tuné
            # n'a pas de sentencepiece.bpe.model ou présente une incompatibilité de fast tokenizer.
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-1.3B")
        # transformers >= 4.56 attend `dtype`, les versions plus anciennes `torch_dtype`.
        import transformers

        major, minor = (int(x) for x in transformers.__version__.split(".")[:2])
        dtype_kw = "dtype" if (major, minor) >= (4, 56) else "torch_dtype"
        base = AutoModelForSeq2SeqLM.from_pretrained(
            settings.nllb_base_model, use_safetensors=True, **rev, **{dtype_kw: dtype}
        )

        # Adaptateurs : un nom par dossier distinct (un dossier partagé = chargé une fois).
        self.adapters: dict[str, str] = {}  # sens "fr-dyu" -> nom d'adaptateur
        self.fingerprints: dict[str, str] = {}
        paths = {"fr-dyu": settings.adapter_fra_dyu, "dyu-fr": settings.adapter_dyu_fra}
        model = base
        loaded: dict[str, str] = {}  # chemin -> nom
        for direction, path in paths.items():
            if not path:
                continue
            if path not in loaded:
                from peft import PeftModel

                adapter_name = f"a{len(loaded)}"
                if not loaded:
                    model = PeftModel.from_pretrained(base, path, adapter_name=adapter_name)
                else:
                    model.load_adapter(path, adapter_name=adapter_name)
                loaded[path] = adapter_name
                self.fingerprints[adapter_name] = _fingerprint(path)
            self.adapters[direction] = loaded[path]

        self.model = model.to(self.device).eval()
        # Le generation_config du modèle fusionné fixe max_length (200, puis 64 en 5c36e48).
        # L'API passe toujours max_new_tokens : transformers avertirait à CHAQUE traduction
        # que les deux sont réglés. On remet max_length à sa valeur par défaut :
        # c'est max_new_tokens (KOUMA_MAX_NEW_TOKENS) qui borne la sortie.
        from transformers import GenerationConfig

        gen_config = getattr(self.model, "generation_config", None)
        if gen_config is not None:
            gen_config.max_length = GenerationConfig().max_length
        if not self.adapters:
            log.info(
                "modele_sans_adaptateur",
                extra={
                    "fields": {
                        "model": settings.nllb_base_model,
                        "revision": settings.nllb_revision or "non figée",
                    }
                },
            )
        self.postprocessor = PostProcessor(settings.postprocess_rules_path)
        idioms_file = ROOT_DIR.parent / "data" / "custom_idioms.json"
        self.idiom_matcher = IdiomMatcher(idioms_file if idioms_file.exists() else None)

    @staticmethod
    def _pick_device(wanted: str) -> str:
        import torch

        if wanted != "auto":
            return wanted
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def translate(self, text: str, src: str, tgt: str) -> str:
        return self.translate_batch([text], src, tgt)[0]

    def translate_batch(self, texts: list[str], src: str, tgt: str) -> list[str]:
        results: list[str | None] = [None] * len(texts)
        missing_indices: list[int] = []
        missing_texts: list[str] = []

        # 1. Vérification dans le glossaire d'expressions figées
        for i, text in enumerate(texts):
            idiom_hit = self.idiom_matcher.match(text, src, tgt)
            if idiom_hit is not None:
                results[i] = idiom_hit
            else:
                missing_indices.append(i)
                missing_texts.append(text)

        # 2. Inférence NLLB pour les textes non trouvés dans le glossaire
        if missing_texts:
            direction = f"{src}-{tgt}"
            adapter = self.adapters.get(direction)
            tok = self.tokenizer
            tok.src_lang = to_nllb(src)
            inputs = tok(missing_texts, return_tensors="pt", padding=True, truncation=True, max_length=256)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            gen_kwargs = dict(
                forced_bos_token_id=tok.convert_tokens_to_ids(to_nllb(tgt)),
                num_beams=self.settings.num_beams,
                max_new_tokens=self.settings.max_new_tokens,
                no_repeat_ngram_size=self.settings.no_repeat_ngram_size,
            )
            with self._torch.inference_mode():
                if adapter is None and hasattr(self.model, "disable_adapter"):
                    # Pas d'adaptateur pour ce sens : modèle de base pur.
                    with self.model.disable_adapter():
                        out = self.model.generate(**inputs, **gen_kwargs)
                else:
                    if adapter is not None:
                        self.model.set_adapter(adapter)
                    out = self.model.generate(**inputs, **gen_kwargs)
            # clean_up_tokenization_spaces=False : sinon l'espace avant « ? » ou « ! » est supprimé.
            decoded = tok.batch_decode(
                out, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            for idx, dec in zip(missing_indices, decoded):
                results[idx] = dec.strip()

        # 3. Post-traitement systématique par règles (corrections d'hallucinations)
        return [self.postprocessor.apply((t or "").strip(), src, tgt) for t in results]

    def info(self) -> dict:
        info = {
            "name": self.name,
            # "model" : un seul modèle chargé (déjà fusionné, ou NLLB de base sans adaptateur).
            # "adapters" : NLLB de base + au moins un adaptateur LoRA.
            "mode": "adapters" if self.adapters else "model",
            "base_model": self.settings.nllb_base_model,
            "revision": self.settings.nllb_revision,
            "device": self.device,
            # Réglages de génération : indispensables pour comparer deux mesures de latence.
            "generation": {
                "num_beams": self.settings.num_beams,
                "max_new_tokens": self.settings.max_new_tokens,
                "no_repeat_ngram_size": self.settings.no_repeat_ngram_size,
            },
            "postprocess_rules_version": self.postprocessor.version,
            "idioms_count": {
                "fr_to_dyu": len(self.idiom_matcher.fr_to_dyu),
                "dyu_to_fr": len(self.idiom_matcher.dyu_to_fr),
            },
        }
        if self.adapters:
            info["directions"] = {
                d: {"adapter": a, "fingerprint": self.fingerprints.get(a)}
                for d, a in self.adapters.items()
            }
            info["directions_base_only"] = [
                d for d in ("fr-dyu", "dyu-fr") if d not in self.adapters
            ]
        return info


def build_translator(settings: Settings) -> Translator:
    if settings.translator_backend == "stub":
        return StubTranslator()
    if settings.translator_backend == "nllb":
        return NllbLoraTranslator(settings)
    raise ValueError(f"KOUMA_TRANSLATOR inconnu : {settings.translator_backend!r}")
