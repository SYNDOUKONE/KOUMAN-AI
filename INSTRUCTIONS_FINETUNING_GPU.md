# Guide de Lancement Fine-Tuning Kouman AI (PC Gamer)

Ce document résume la procédure pour lancer l'entraînement du modèle NLLB-200 1.3B LoRA sur une machine avec GPU (NVIDIA).

## 1. Pré-requis
- Python 3.10+
- GPU NVIDIA avec CUDA installé
- Installation des dépendances :
  ```bash
  pip install torch transformers datasets peft sacrebleu pandas accelerate
  ```

## 2. Configuration pour PC Gamer
Le script `scripts/finetune_nllb.py` est configuré par défaut pour être très léger (MPS/iMac). Sur un PC gamer avec une bonne carte NVIDIA (ex: RTX 3080/4090), tu peux augmenter les performances :

- **Ligne 34 (BATCH_SIZE)** : Tu peux passer de `2` à `4` ou `8` selon ta VRAM.
- **Ligne 35 (GRAD_ACCUM)** : Si tu augmentes le batch size, tu peux réduire l'accumulation (ex: `8`) pour garder un batch effectif de 32.
- **Ligne 192 (fp16)** : Change `fp16=False` en `fp16=True` pour utiliser la précision mixte (accélère énormément l'entraînement sur NVIDIA).

## 3. Commande de lancement
Pour lancer l'entraînement et sauvegarder les logs dans un fichier pour les consulter plus tard :

```bash
python scripts/finetune_nllb.py > scripts/finetune_v2.log 2>&1 &
```

## 4. Suivi de l'avancement
Pour voir si ça avance en temps réel :
```bash
tail -f scripts/finetune_v2.log
```

## 5. Résultat
Une fois terminé, le modèle sera sauvegardé dans :
`models/nllb_lora_dioula/final`
