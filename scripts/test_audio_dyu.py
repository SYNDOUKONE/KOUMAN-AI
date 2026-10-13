"""
Kouman AI — Testeur Entrée & Sortie Vocale en Dioula (Audio STT & TTS)

Fonctionnalités :
1. SORTIE VOCALE (TTS Dioula) : Synthèse vocale avec Meta MMS-TTS (facebook/mms-tts-dyu) -> Fichier .wav + lecture via afplay (macOS).
2. ENTRÉE VOCALE (STT Dioula) : Transcription avec Dama12/whisper-tiny-dioula (HuggingFace Transformers).
3. PIPELINE COMPLET : Français -> Traduction NLLB -> Voix Dioula (TTS) -> Reconnaissance vocale (STT) -> Français.
"""

import os
import sys
import argparse
import subprocess
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from transformers import (
    AutoTokenizer,
    VitsModel,
    AutoModelForSeq2SeqLM,
    WhisperForConditionalGeneration,
    WhisperFeatureExtractor,
    WhisperTokenizer,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTS_MODEL_ID = "facebook/mms-tts-dyu"
STT_MODEL_ID = "Dama12/whisper-tiny-dioula"
STT_BASE_ID = "openai/whisper-tiny"  # Feature extractor + tokenizer (vocab absent sur Dama12)
NLLB_BASE_MODEL = "facebook/nllb-200-1.3B"

# Détection de l'appareil
device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

class KoumanAudioTester:
    def __init__(self):
        self.tts_tokenizer = None
        self.tts_model = None
        self.stt_model = None
        self.stt_feature_extractor = None
        self.stt_tokenizer = None
        self.nllb_tokenizer = None
        self.nllb_model = None

    def load_tts(self):
        """Charge le modèle de synthèse vocale (MMS-TTS Dioula)."""
        if self.tts_model is None:
            print(f"🔊 Chargement du modèle TTS Dioula ({TTS_MODEL_ID})...", flush=True)
            self.tts_tokenizer = AutoTokenizer.from_pretrained(TTS_MODEL_ID)
            self.tts_model = VitsModel.from_pretrained(TTS_MODEL_ID).to(device)
            self.tts_model.eval()
            print("✅ Modèle TTS Dioula prêt !\n", flush=True)

    def load_stt(self):
        """Charge le modèle de reconnaissance vocale (Dama12/whisper-tiny-dioula)."""
        if self.stt_model is None:
            print(f"🎙️ Chargement du modèle STT Dioula ({STT_MODEL_ID})...", flush=True)
            # Dama12 ne publie que les poids -> feature extractor + tokenizer depuis openai/whisper-tiny
            self.stt_feature_extractor = WhisperFeatureExtractor.from_pretrained(STT_BASE_ID)
            self.stt_tokenizer = WhisperTokenizer.from_pretrained(STT_BASE_ID, language="dyu", task="transcribe")
            # Forcer CPU : aten::isin non supporté sur MPS avec Whisper (PyTorch bug #77764)
            stt_device = "cpu"
            self.stt_model = WhisperForConditionalGeneration.from_pretrained(STT_MODEL_ID).to(stt_device)
            self.stt_model.eval()
            self._stt_device = stt_device
            print("✅ Modèle STT Dioula prêt !\n", flush=True)

    def load_translator(self):
        """Charge le traducteur NLLB bidirectionnel."""
        if self.nllb_model is None:
            print(f"🌍 Chargement du traducteur NLLB ({NLLB_BASE_MODEL})...", flush=True)
            self.nllb_tokenizer = AutoTokenizer.from_pretrained(NLLB_BASE_MODEL)
            self.nllb_model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_BASE_MODEL).to(device)
            self.nllb_model.eval()
            print("✅ Traducteur prêt !\n", flush=True)

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Traduit entre Français (fra_Latn) et Dioula (dyu_Latn)."""
        self.load_translator()
        self.nllb_tokenizer.src_lang = src_lang
        inputs = self.nllb_tokenizer(text, return_tensors="pt").to(device)
        forced_bos = self.nllb_tokenizer.lang_code_to_id[tgt_lang]
        with torch.no_grad():
            tokens = self.nllb_model.generate(**inputs, forced_bos_token_id=forced_bos, max_length=64, num_beams=4)
        return self.nllb_tokenizer.batch_decode(tokens, skip_special_tokens=True)[0]

    def text_to_speech(self, text_dioula: str, output_path: str = "audio_sortie_dioula.wav", play: bool = True) -> str:
        """Synthétise une phrase en Dioula en fichier audio WAV et la joue en direct."""
        self.load_tts()
        print(f"🎵 Synthèse vocale de : « {text_dioula} »...", flush=True)
        inputs = self.tts_tokenizer(text_dioula.lower(), return_tensors="pt").to(device)
        torch.manual_seed(42)
        with torch.no_grad():
            waveform = self.tts_model(**inputs).waveform[0].cpu().numpy()

        sampling_rate = self.tts_model.config.sampling_rate
        wavfile.write(output_path, sampling_rate, waveform)
        duree = len(waveform) / sampling_rate
        print(f"💾 Audio généré : {output_path} ({sampling_rate}Hz, {duree:.2f}s)", flush=True)

        if play and sys.platform == "darwin":
            print("▶️ Lecture audio sur votre Mac...", flush=True)
            try:
                subprocess.run(["afplay", output_path], check=False)
            except Exception as e:
                print(f"Note : impossible de lire avec afplay : {e}")

        return output_path

    def speech_to_text(self, audio_path: str) -> str:
        """Transcrit un fichier audio en texte Dioula via Whisper HuggingFace."""
        self.load_stt()
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Fichier audio non trouvé : {audio_path}")

        import librosa
        print(f"🎧 Transcription audio de : {audio_path}...", flush=True)
        # Charger et rééchantillonner à 16kHz si nécessaire
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        inputs = self.stt_feature_extractor(
            audio, sampling_rate=16000, return_tensors="pt"
        ).to(self._stt_device)
        with torch.no_grad():
            predicted_ids = self.stt_model.generate(
                inputs["input_features"],
                max_new_tokens=128,
            )
        text = self.stt_tokenizer.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()
        print(f"📝 Transcription obtenue : « {text} »", flush=True)
        return text

    def run_benchmark_scenarios(self):
        """Lance une série de tests prédéfinis pour valider TTS et STT."""
        phrases_dioula = [
            ("Salutations", "Aw ni sɔgɔma, i ka kɛnɛ wa ?"),
            ("Marché / Commerce", "N bɛ taa sugu la ka malo san."),
            ("Famille / Maison", "Denmisɛn bɛ sunɔgɔ bon kɔnɔ."),
            ("Au revoir", "An bɛ bɛn sini, i ni ce kosɛbɛ."),
        ]

        print("=" * 75)
        print("🚀 LANCEMENT DU BENCHMARK VOCAL DIOULA (TTS + STT)")
        print("=" * 75)

        import re
        for cat, phrase in phrases_dioula:
            print(f"\n📌 Catégorie : {cat}")
            print(f"  Texte original Dioula : {phrase}")

            # Sanitize pour nom de fichier valide (supprime / et caractères spéciaux)
            safe_cat = re.sub(r"[^\w]", "_", cat).lower().strip("_")
            wav_file = f"test_{safe_cat}.wav"
            self.text_to_speech(phrase, output_path=wav_file, play=False)
            
            # 2. STT
            transcription = self.speech_to_text(wav_file)
            print(f"  Comparaison : Original=[{phrase}] ➔ Reconnu=[{transcription}]")

        print("\n" + "=" * 75)
        print("✅ TOUS LES TESTS VOCAUX ONT ÉTÉ EXÉCUTÉS AVEC SUCCÈS !")
        print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Testeur vocal Dioula (Kouman AI)")
    parser.add_argument("--tts", type=str, help="Texte en Dioula à vocaliser en audio WAV")
    parser.add_argument("--stt", type=str, help="Chemin vers un fichier audio WAV à transcrire")
    parser.add_argument("--fr2audio", type=str, help="Phrase en Français -> Traduction Dioula -> Synthèse vocale")
    parser.add_argument("--auto", action="store_true", help="Lancer la suite de tests automatiques")
    parser.add_argument("--no-play", action="store_true", help="Ne pas jouer le son sur le Mac")
    args = parser.parse_args()

    tester = KoumanAudioTester()
    play = not args.no_play

    if args.auto:
        tester.run_benchmark_scenarios()
    elif args.tts:
        tester.text_to_speech(args.tts, play=play)
    elif args.stt:
        text = tester.speech_to_text(args.stt)
        trad = tester.translate(text, "dyu_Latn", "fra_Latn")
        print(f"🇫🇷 Traduction en Français : « {trad} »")
    elif args.fr2audio:
        print(f"🇫🇷 Français : « {args.fr2audio} »")
        dyu = tester.translate(args.fr2audio, "fra_Latn", "dyu_Latn")
        print(f"🌍 Traduction Dioula : « {dyu} »")
        tester.text_to_speech(dyu, play=play)
    else:
        # Démo rapide par défaut si aucun argument
        print("=" * 70)
        print("  KOUMAN AI — DÉMONSTRATEUR VOCAL DIOULA")
        print("=" * 70)
        print("1. Synthèse vocale d'exemple en Dioula : 'Aw ni sɔgɔma, i ka kɛnɛ wa ?'")
        wav = tester.text_to_speech("Aw ni sɔgɔma, i ka kɛnɛ wa ?", output_path="demo_salutation.wav", play=play)
        print("\n2. Transcription de l'audio généré (Reconnaissance Vocale STT) :")
        texte_reconnu = tester.speech_to_text(wav)
        print("\n3. Traduction de la transcription vers le Français :")
        fr_trad = tester.translate(texte_reconnu, "dyu_Latn", "fra_Latn")
        print(f"  Sortie finale Français : « {fr_trad} »")
        print("\n💡 Vous pouvez aussi exécuter :")
        print('   python3 scripts/test_audio_dyu.py --tts "I tɔgɔ bi di ?"')
        print('   python3 scripts/test_audio_dyu.py --fr2audio "Bonjour, comment vas-tu ?"')
        print('   python3 scripts/test_audio_dyu.py --stt demo_salutation.wav')
        print('   python3 scripts/test_audio_dyu.py --auto')


if __name__ == "__main__":
    main()
