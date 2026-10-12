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

from app.core.config import Settings
from app.core.languages import to_nllb

log = logging.getLogger("kouma")


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
        self.tokenizer = AutoTokenizer.from_pretrained(settings.nllb_base_model)
        # transformers >= 4.56 attend `dtype`, les versions plus anciennes `torch_dtype`.
        import transformers

        major, minor = (int(x) for x in transformers.__version__.split(".")[:2])
        dtype_kw = "dtype" if (major, minor) >= (4, 56) else "torch_dtype"
        base = AutoModelForSeq2SeqLM.from_pretrained(
            settings.nllb_base_model, use_safetensors=True, **{dtype_kw: dtype}
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
        self.postprocessor = PostProcessor(settings.postprocess_rules_path)

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
        direction = f"{src}-{tgt}"
        adapter = self.adapters.get(direction)
        tok = self.tokenizer
        tok.src_lang = to_nllb(src)
        inputs = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=256)
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
        return [self.postprocessor.apply(t.strip(), src, tgt) for t in decoded]

    def info(self) -> dict:
        return {
            "name": self.name,
            "base_model": self.settings.nllb_base_model,
            "device": self.device,
            "directions": {
                d: {"adapter": a, "fingerprint": self.fingerprints.get(a)}
                for d, a in self.adapters.items()
            },
            "directions_base_only": [d for d in ("fr-dyu", "dyu-fr") if d not in self.adapters],
            "postprocess_rules_version": self.postprocessor.version,
        }


def build_translator(settings: Settings) -> Translator:
    if settings.translator_backend == "stub":
        return StubTranslator()
    if settings.translator_backend == "nllb":
        return NllbLoraTranslator(settings)
    raise ValueError(f"KOUMA_TRANSLATOR inconnu : {settings.translator_backend!r}")
