"""NllbLoraTranslator sur un MINI modèle NLLB construit localement (aucun réseau).

Vérifie les deux façons de charger le traducteur :
- un modèle déjà fusionné (ex. syndou/nllb-200-dioula) sans adaptateur ;
- NLLB de base + adaptateur LoRA.
Ignoré si torch / transformers / sentencepiece ne sont pas installés (cas de la CI).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
spm = pytest.importorskip("sentencepiece")

from app.core.config import Settings  # noqa: E402
from app.services.translator import NllbLoraTranslator  # noqa: E402

PHRASES = ["Bonjour, comment allez-vous ?", "I ni ce, i ka kɛnɛ wa ?", "Merci beaucoup."] * 20


@pytest.fixture(scope="module")
def tiny_model_dir(tmp_path_factory):
    """Mini NLLB (2 couches, vocab ~300) sauvegardé comme un modèle Hugging Face."""
    from transformers import M2M100Config, M2M100ForConditionalGeneration, NllbTokenizer

    root = tmp_path_factory.mktemp("tiny_nllb")
    corpus = root / "corpus.txt"
    corpus.write_text("\n".join(PHRASES), encoding="utf-8")
    spm.SentencePieceTrainer.train(
        input=str(corpus),
        model_prefix=str(root / "spm"),
        vocab_size=32,
        character_coverage=1.0,
        bos_id=0,
        pad_id=1,
        eos_id=2,
        unk_id=3,
    )
    tok = NllbTokenizer(vocab_file=str(root / "spm.model"))
    torch.manual_seed(0)
    config = M2M100Config(
        vocab_size=len(tok),
        d_model=16,
        encoder_layers=1,
        decoder_layers=1,
        encoder_attention_heads=2,
        decoder_attention_heads=2,
        encoder_ffn_dim=32,
        decoder_ffn_dim=32,
        max_position_embeddings=128,
        pad_token_id=tok.pad_token_id,
        bos_token_id=tok.bos_token_id,
        eos_token_id=tok.eos_token_id,
        decoder_start_token_id=tok.eos_token_id,
    )
    model = M2M100ForConditionalGeneration(config)
    out = root / "model"
    model.save_pretrained(out, safe_serialization=True)
    tok.save_pretrained(out)
    return out


def _settings(model_dir, **kw) -> Settings:
    return replace(
        Settings(),
        translator_backend="nllb",
        nllb_base_model=str(model_dir),
        device="cpu",
        num_beams=1,
        max_new_tokens=8,
        **kw,
    )


def test_merged_model_without_adapter(tiny_model_dir):
    tr = NllbLoraTranslator(_settings(tiny_model_dir))
    out = tr.translate("Bonjour, comment allez-vous ?", "fr", "dyu")
    assert isinstance(out, str)
    info = tr.info()
    assert info["mode"] == "model"
    assert info["base_model"] == str(tiny_model_dir)
    assert "directions" not in info  # pas d'adaptateur : rien de trompeur à afficher


def test_revision_is_reported(tiny_model_dir):
    # Avec un dossier local, transformers ignore la révision ; on vérifie qu'elle est exposée.
    tr = NllbLoraTranslator(_settings(tiny_model_dir, nllb_revision=None))
    assert tr.info()["revision"] is None


def test_base_plus_lora_adapter_still_works(tiny_model_dir, tmp_path):
    peft = pytest.importorskip("peft")
    from transformers import AutoModelForSeq2SeqLM

    base = AutoModelForSeq2SeqLM.from_pretrained(tiny_model_dir)
    lora = peft.get_peft_model(
        base, peft.LoraConfig(r=2, lora_alpha=4, target_modules=["q_proj", "v_proj"])
    )
    adapter_dir = tmp_path / "adapter"
    lora.save_pretrained(adapter_dir)

    tr = NllbLoraTranslator(
        _settings(tiny_model_dir, adapter_fra_dyu=str(adapter_dir), adapter_dyu_fra=None)
    )
    assert isinstance(tr.translate("Merci beaucoup.", "fr", "dyu"), str)
    info = tr.info()
    assert info["mode"] == "adapters"
    assert set(info["directions"]) == {"fr-dyu"}
    assert info["directions_base_only"] == ["dyu-fr"]
