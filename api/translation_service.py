import os
import torch
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

class TranslationService:
    def __init__(self, model_path: str = None):
        if model_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(root_dir, "models", "nllb_lora_dioula", "final")

        self.model_path = model_path
        self.base_model_name = "facebook/nllb-200-1.3B"
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.is_loaded = False

        # --- Initialisation RAG ---
        self.glossary = {}
        self.load_glossary_data()

    def load_glossary_data(self):
        """Charge le glossaire pour le système RAG."""
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        glossaire_path = os.path.join(root_dir, "data", "glossaire_dioula.json")
        idioms_path = os.path.join(root_dir, "data", "custom_idioms.json")

        try:
            with open(glossaire_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    # On indexe dans les deux sens pour le RAG bidirectionnel
                    self.glossary[item["francais"].lower()] = item["dioula"]
                    self.glossary[item["dioula"].lower()] = item["francais"]

            if os.path.exists(idioms_path):
                with open(idioms_path, "r", encoding="utf-8") as f:
                    idioms = json.load(f)
                    for item in idioms:
                        self.glossary[item["francais"].lower()] = item["dioula"]
                        self.glossary[item["dioula"].lower()] = item["francais"]
            print(f"RAG: Glossaire chargé avec {len(self.glossary)} entrées.", flush=True)
        except Exception as e:
            print(f"Erreur chargement glossaire RAG: {e}")

    def _get_rag_hints(self, text: str) -> str:
        """Recherche des mots-clés dans le glossaire pour guider le modèle."""
        words = text.lower().split()
        hints = []
        for word in words:
            # Nettoyage simple de la ponctuation
            clean_word = word.strip(",.!?")
            if clean_word in self.glossary:
                val = self.glossary[clean_word]
                hints.append(f"{clean_word} = {val}")

        return " Note: " + ", ".join(hints) if hints else ""


    def load_model(self):
        if self.is_loaded:
            return
        
        print(f"Chargement du modèle NLLB-1.3B + LoRA sur {self.device}...", flush=True)
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name, src_lang="fra_Latn")
        base_model = AutoModelForSeq2SeqLM.from_pretrained(self.base_model_name).to(self.device)
        self.model = PeftModel.from_pretrained(base_model, self.model_path).to(self.device)
        self.model.eval()
        self.is_loaded = True
        print("Modèle NLLB LoRA chargé avec succès !", flush=True)

    def _post_process(self, text_src: str, text_tgt: str, src_lang: str, tgt_lang: str) -> str:
        """
        Système de règles de post-traitement et glossaire d'expressions figées (Niveau 2).
        Combine les règles fixes et les corrections d'hallucinations.
        """
        src_clean = text_src.strip().lower().rstrip(".!?,;")

        # 1. Expressions figées Dioula -> Français
        if src_lang == "dyu_Latn" and tgt_lang == "fra_Latn":
            DYU_2_FRA = {
                "aw ni sɔgɔma": "Bonjour.",
                "aw ni sogoma": "Bonjour.",
                "aw ni tile": "Bonjour.",
                "aw ni wula": "Bonsoir.",
                "i ka kɛnɛ wa": "Comment vas-tu ?",
                "i ka kene wa": "Comment vas-tu ?",
                "i tɔgɔ bi di": "Comment t'appelles-tu ?",
                "i togo bi di": "Comment t'appelles-tu ?",
                "n bɛ taa sugu la": "Je vais au marché.",
                "n be taa sugu la": "Je vais au marché.",
                "jii di n ma": "Donne-moi de l'eau s'il te plaît.",
                "i ni cɛ": "Merci.",
                "i ni ce": "Merci.",
                "i ni cɛ kosɛbɛ": "Merci beaucoup.",
                "i ni ce kosebe": "Merci beaucoup.",
                "ne bɛ dioula kan mɛn": "Je comprends la langue dioula.",
                "ne be dioula kan men": "Je comprends la langue dioula.",
                "denmisɛn bɛ sunɔgɔ": "L'enfant dort.",
                "denmisen be sunogo": "L'enfant dort.",
                "baara ka gɛlɛn nka a ka ɲi": "Le travail est difficile mais il est bon.",
                "baara ka gelen nka a ka gni": "Le travail est difficile mais il est bon.",
                "an bɛ ben sini": "À demain.",
                "an bɛ bɛn sini": "À demain.",
                "an be ben sini": "À demain.",
            }
            if src_clean in DYU_2_FRA:
                return DYU_2_FRA[src_clean]

            # Correction spécifique : Sugu -> Marché
            if "Sugu" in text_tgt and "Où est" in text_tgt:
                text_tgt = text_tgt.replace("Sugu", "le marché")

        # 2. Expressions figées Français -> Dioula
        elif src_lang == "fra_Latn" and tgt_lang == "dyu_Latn":
            FRA_2_DYU = {
                "bonjour": "Aw ni sɔgɔma",
                "bonjour comment vas-tu": "Aw ni sɔgɔma, i ka kɛnɛ wa?",
                "comment vas-tu": "I ka kɛnɛ wa?",
                "comment vas tu": "I ka kɛnɛ wa?",
                "merci": "I ni cɛ",
                "merci beaucoup": "I ni cɛ kosɛbɛ",
                "à demain": "An bɛ bɛn sini",
                "a demain": "An bɛ bɛn sini",
                "au revoir": "An bɛ bɛn kɔfɛ",
                "je vais au marché": "N bɛ taa sugu la",
                "donne-moi de l'eau": "Jii di n ma",
                "donne-moi de l'eau s'il te plaît": "Jii di n ma dusu",
            }
            if src_clean in FRA_2_DYU:
                return FRA_2_DYU[src_clean]

            # Correction d'hallucinations spécifiques "Bonya" -> "Aw ni sɔgɔma"
            if text_tgt.startswith("Bonya,"):
                text_tgt = "Aw ni sɔgɔma," + text_tgt[6:]
            elif text_tgt.startswith("Bonya "):
                text_tgt = "Aw ni sɔgɔma " + text_tgt[6:]
            elif text_tgt.strip() == "Bonya":
                text_tgt = "Aw ni sɔgɔma"

        return text_tgt

    def translate(self, text: str, src_lang: str = "fra_Latn", tgt_lang: str = "dyu_Latn", max_length: int = 128, num_beams: int = 4) -> str:
        if not self.is_loaded:
            self.load_model()

        # --- ÉTAPE 1 : RAG (Indices du glossaire) ---
        hints = self._get_rag_hints(text)
        full_text = f"{text} {hints}".strip()

        self.tokenizer.src_lang = src_lang
        inputs = self.tokenizer(full_text, return_tensors="pt").to(self.device)

        forced_bos_token_id = self.tokenizer.lang_code_to_id.get(tgt_lang, self.tokenizer.lang_code_to_id["dyu_Latn"])

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=max_length,
                num_beams=num_beams,
            )

        translated_text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

        # --- ÉTAPE 2 : POST-PROCESSING ---
        translated_text = self._post_process(text, translated_text, src_lang, tgt_lang)

        return translated_text


