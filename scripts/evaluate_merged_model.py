"""
Évaluation du modèle fusionné officiel syndou/nllb-200-dioula sur le Test Sacré (144 phrases).
Mesure BLEU et chrF++ dans les deux sens : FR -> DYU et DYU -> FR.
Met à jour data/baselines_results.tsv.
"""

import os
import torch
import pandas as pd
import sacrebleu
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_SACRE_PATH = os.path.join(ROOT_DIR, "data", "test_sacre.csv")
OUT_TSV_PATH = os.path.join(ROOT_DIR, "data", "baselines_results.tsv")
MODEL_ID = "syndou/nllb-200-dioula"
REVISION = "5c36e481ce9ce8d6f73a57181fb93d6900ddad89"

device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

def evaluate_direction(model, tokenizer, pairs, src_lang, tgt_lang, label_dir):
    print(f"\n--- Évaluation Direction : {label_dir} ({len(pairs)} phrases) ---", flush=True)
    src_texts = [p["src"] for p in pairs]
    refs = [p["tgt"] for p in pairs]
    
    tokenizer.src_lang = src_lang
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)
    
    predictions = []
    batch_size = 16
    for i in range(0, len(src_texts), batch_size):
        batch = src_texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=96).to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=96,
                num_beams=4
            )
        preds = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        predictions.extend(preds)
        print(f"  Avancement: {len(predictions)}/{len(src_texts)}...", flush=True)
        
    bleu = sacrebleu.corpus_bleu(predictions, [refs])
    chrf = sacrebleu.corpus_chrf(predictions, [refs], word_order=2)
    
    print(f"  Résultat {label_dir} : BLEU = {bleu.score:.2f} | chrF++ = {chrf.score:.2f}", flush=True)
    return {
        "Modèle": f"NLLB Fusionné ({REVISION[:7]})",
        "Dataset": "Test Sacré",
        "Direction": label_dir,
        "chrF++": round(chrf.score, 2),
        "BLEU": round(bleu.score, 2),
        "Échantillons": len(pairs)
    }

def main():
    print(f"Chargement du Test Sacré depuis {TEST_SACRE_PATH}...")
    df = pd.read_csv(TEST_SACRE_PATH).dropna(subset=["fr", "dyu"])
    
    pairs_fr2dyu = [{"src": row["fr"], "tgt": row["dyu"]} for _, row in df.iterrows()]
    pairs_dyu2fr = [{"src": row["dyu"], "tgt": row["fr"]} for _, row in df.iterrows()]
    
    print(f"Chargement du tokenizer et du modèle sur {device}...")
    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-1.3B")
    
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID, revision=REVISION).to(device)
    model.eval()
    
    res_fr2dyu = evaluate_direction(model, tokenizer, pairs_fr2dyu, "fra_Latn", "dyu_Latn", "FR -> DYU")
    res_dyu2fr = evaluate_direction(model, tokenizer, pairs_dyu2fr, "dyu_Latn", "fra_Latn", "DYU -> FR")
    
    # Mise à jour du TSV
    df_tsv = pd.read_csv(OUT_TSV_PATH, sep="\t") if os.path.exists(OUT_TSV_PATH) else pd.DataFrame()
    # Supprimer les anciennes lignes éventuelles pour ce modèle sur Test Sacré
    if not df_tsv.empty:
        df_tsv = df_tsv[~((df_tsv["Modèle"].str.contains("Fusionné", na=False)) & (df_tsv["Dataset"] == "Test Sacré"))]
    
    new_rows = pd.DataFrame([res_fr2dyu, res_dyu2fr])
    df_updated = pd.concat([df_tsv, new_rows], ignore_index=True)
    df_updated.to_csv(OUT_TSV_PATH, sep="\t", index=False)
    
    print("\n" + "=" * 75)
    print("TABLEAU COMPLET BASILINES & TEST SACRE")
    print("=" * 75)
    print(df_updated.to_string(index=False))
    print(f"\n✅ Fichier mis à jour : {OUT_TSV_PATH}")

if __name__ == "__main__":
    main()
