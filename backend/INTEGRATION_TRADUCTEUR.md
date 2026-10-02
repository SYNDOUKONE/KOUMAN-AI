# Livrer un nouvel adaptateur à l'API (pôle NLP)

L'API charge `facebook/nllb-200-1.3B` puis un adaptateur LoRA **par sens de traduction**. Aucune ligne de code à modifier : tout passe par la configuration.

## Ce qu'il faut livrer

Un dossier versionné, par exemple `nllb_lora_dioula_v2/`, contenant :

- `adapter_config.json` et `adapter_model.safetensors` (sortie de `model.save_pretrained`) ;
- un `README.md` : données, découpage, hyperparamètres, graine, et scores **avec métrique, sens et jeu de test** ;
- les paramètres de génération recommandés (`num_beams`, `max_new_tokens`, `no_repeat_ngram_size`).

Le modèle de base doit être celui indiqué dans `adapter_config.json` → `base_model_name_or_path`.

## Comment l'API le charge

| Cas | Configuration |
|---|---|
| Adaptateur bidirectionnel (un seul dossier) | `KOUMA_ADAPTER_FRA_DYU` et `KOUMA_ADAPTER_DYU_FRA` = même dossier |
| Un adaptateur par sens | un dossier dans chaque variable |
| Pas d'adaptateur pour un sens | laisser la variable vide → modèle de base |

Un dossier partagé n'est chargé qu'une fois en mémoire.

Codes de langue : l'API parle en `fr` / `dyu` / `bam` et les convertit en `fra_Latn` / `dyu_Latn` / `bam_Latn` (fichier `app/core/languages.py`). L'entraînement doit donc utiliser exactement ces codes NLLB, dans les deux sens pour un adaptateur bidirectionnel.

## Vérifier après livraison

1. `pytest -m model` avec les variables ci-dessus : une traduction non vide dans chaque sens.
2. `GET /health` → `translator.directions` : l'**empreinte** (12 caractères) de chaque sens. Noter cette empreinte dans le README de l'adaptateur : c'est ainsi qu'on sait quelle version a servi pendant une démo.

## Règles de post-traitement

Les corrections de sortie (ex. remplacer un mot mal traduit) ne vont **pas** dans le code : elles vont dans `config/postprocess_rules.json`, avec le sens (`fr-dyu`), l'expression régulière, le remplacement, la **raison** et un drapeau `enabled`. Chaque règle doit être validée par un locuteur.
