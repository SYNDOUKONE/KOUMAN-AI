import os
from huggingface_hub import HfApi

TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "syndou/nllb-lora-dioula"
LOCAL_FOLDER = "models/nllb_lora_dioula/final"

def upload():
    print(f"Connexion à Hugging Face et upload vers {REPO_ID}...", flush=True)
    api = HfApi()
    
    try:
        api.upload_folder(
            folder_path=LOCAL_FOLDER,
            repo_id=REPO_ID,
            repo_type="model",
            token=TOKEN,
        )
        print("\n✅ Modèle uploadé avec succès sur Hugging Face !", flush=True)
    except Exception as e:
        print(f"\n❌ Erreur lors de l'upload : {e}", flush=True)

if __name__ == "__main__":
    upload()
