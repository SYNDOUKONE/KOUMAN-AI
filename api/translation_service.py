import os
import torch
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

    def translate(self, text: str, src_lang: str = "fra_Latn", tgt_lang: str = "dyu_Latn", max_length: int = 128, num_beams: int = 4) -> str:
        if not self.is_loaded:
            self.load_model()

        self.tokenizer.src_lang = src_lang
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        
        forced_bos_token_id = self.tokenizer.lang_code_to_id.get(tgt_lang, self.tokenizer.lang_code_to_id["dyu_Latn"])
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=max_length,
                num_beams=num_beams,
            )
        
        translated_text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        return translated_text
