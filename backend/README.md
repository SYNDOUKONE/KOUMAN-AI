# KOUMA AI — API (v0.3.1)

Chatbot et traduction français ↔ dioula. Pipeline :

```
message dioula ──► traduction dyu→fr ──► LLM (français) ──► traduction fr→dyu ──► réponse dioula
                                  ▲                                 │
                                  └──── historique EN FRANÇAIS ◄────┘
```

L'historique est gardé en français et n'est jamais retraduit : chaque tour ne coûte que deux traductions.

## 1. Démarrer sans modèle (5 minutes)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q                                          # 39 tests, sans GPU ni réseau
python -m scripts.manage_keys create demo          # note la clé kma_... affichée
cp .env.example .env                               # puis remplir .env (jamais commité)
uvicorn app.main:app --env-file .env --reload
```

**`--env-file .env` est obligatoire** : `config.py` lit uniquement les variables d'environnement, il ne charge pas `.env` tout seul. Sans cette option, l'API démarre en mode factice (stub).

Documentation interactive : http://localhost:8000/docs

Par défaut tout est factice (« stub ») : les réponses contiennent `[stub dyu→fr]`. C'est voulu : on construit et on teste la tuyauterie sans attendre le modèle.

## 2. Brancher le vrai modèle

```bash
# RTX série 50 (Blackwell) : PyTorch compilé pour CUDA 12.8 ou plus
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-model.txt
```

**Option A — modèle fusionné de Syndoux (recommandée depuis le 12/10/2026).** Un seul modèle complet, sans adaptateur (données d'entraînement : voir le README racine). Dans `.env` :

```bash
KOUMA_TRANSLATOR=nllb
KOUMA_NLLB_BASE_MODEL=syndou/nllb-200-dioula
KOUMA_NLLB_REVISION=5c36e481ce9ce8d6f73a57181fb93d6900ddad89   # 13/10 : mêmes poids que 6763611, generation_config corrigé
KOUMA_ADAPTER_FRA_DYU=
KOUMA_ADAPTER_DYU_FRA=
```

Le premier démarrage télécharge le modèle (~2,6 Go) dans le cache Hugging Face. `/health` doit afficher `"mode": "model"`, le nom du modèle et la révision. On ne change `KOUMA_NLLB_REVISION` qu'après avoir comparé la nouvelle version sur le jeu de test gelé.

**Option B — NLLB de base + adaptateur LoRA (ancienne méthode, adaptateur v2 du 02/10).**

```bash
python -c "from huggingface_hub import snapshot_download as d; d('syndou/nllb-lora-dioula', revision='160d1a916d77677c9957d51a91ee120c450a9468', local_dir='models/nllb_lora_dioula_v2')"
KOUMA_NLLB_BASE_MODEL=facebook/nllb-200-1.3B
KOUMA_ADAPTER_FRA_DYU=models/nllb_lora_dioula_v2
KOUMA_ADAPTER_DYU_FRA=models/nllb_lora_dioula_v2   # même dossier : adaptateur bidirectionnel
```

Dans ce cas `/health` affiche `"mode": "adapters"` et l'empreinte `5c3e584130c8` pour les deux sens. Le dossier `models/` est ignoré par git.

Configuration testée : GTX 1650 Ti (4 Go), fp16, `KOUMA_MAX_CONCURRENT_TRANSLATIONS=1`, environ 2 s par traduction courte. Si la mémoire GPU manque : `KOUMA_NUM_BEAMS=2`, puis `KOUMA_DEVICE=cpu`.

- Option B : un adaptateur **par sens**. Un sens sans adaptateur utilise le modèle chargé sans adaptateur.
- `GET /health` affiche, pour chaque sens, l'adaptateur et l'**empreinte** de ses poids : on sait toujours quelle version tourne.
- Le premier démarrage télécharge `facebook/nllb-200-1.3B` (~5 Go). Pendant le chargement, `/health` répond `"status": "chargement"` et les autres routes 503.
- Test avec le vrai modèle : `pytest -m model` (voir `tests/test_model_integration.py`).

Pour le LLM : `export KOUMA_LLM=openrouter OPENROUTER_API_KEY=...` (modèle par défaut `anthropic/claude-sonnet-5`, changeable avec `KOUMA_OPENROUTER_MODEL`), ou `KOUMA_LLM=gemini GEMINI_API_KEY=...`. La clé ne vient **que** de l'environnement, jamais d'une requête.

## 3. Utiliser l'API

Toutes les routes `/api/v1/*` (sauf `/languages`) exigent l'en-tête `X-API-Key`.

```bash
KEY=kma_...
curl -s localhost:8000/api/v1/translate -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"text": "Bonjour, comment vas-tu ?", "src": "fr", "tgt": "dyu"}'

curl -s "localhost:8000/api/v1/chat?debug=true" -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"session_id": "user-42", "lang": "dyu", "message": "<phrase dioula>"}'
```

Python :

```python
import httpx

r = httpx.post(
    "http://localhost:8000/api/v1/chat",
    headers={"X-API-Key": KEY},
    json={"session_id": "user-42", "lang": "dyu", "message": "<phrase dioula>"},
)
print(r.json()["reply"])
```

JavaScript :

```js
const r = await fetch("http://localhost:8000/api/v1/chat", {
  method: "POST",
  headers: { "X-API-Key": KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ session_id: "user-42", lang: "dyu", message: "<phrase dioula>" }),
});
console.log((await r.json()).reply);
```

Test rapide d'un serveur lancé : `python -m scripts.smoke_api --key $KEY --dyu "<phrase validée>"`.

### Mesurer qualité et latence : `scripts/run_scenarios.py`

Rejoue une liste de messages sur `/chat?debug=true` et écrit un CSV par passage : textes (`message`, `fr_input`, `fr_reply`, `reply`), temps par étape (`mt_in`, `llm`, `mt_out`), statut, repli, et la configuration lue dans `/health` (modèle, révision, `num_beams`, appareil, LLM).

```bash
# 1. Remplir docs/scenarios_dyu.csv avec des phrases VALIDÉES par un locuteur (id,lang,message,categorie)
# 2. Lancer une série par réglage, avec un nom explicite
python -m scripts.run_scenarios --key $KEY --label gtx1650-beams4 --repeat 3
# changer KOUMA_NUM_BEAMS=2 dans .env, relancer uvicorn, puis :
python -m scripts.run_scenarios --key $KEY --label gtx1650-beams2 --repeat 3
```

- Résultats : `docs/scenarios_results/<date>_<label>.csv`, lisible dans Excel ou LibreOffice. Le script affiche aussi la médiane et le maximum de chaque étape.
- Par défaut, chaque message ouvre une session neuve : les temps sont comparables d'un passage à l'autre. `--chain` joue tous les messages dans une seule conversation, pour tester l'historique.
- Un seul réglage changé entre deux passages, et toujours le même fichier d'entrée. Les chiffres de référence se mesurent sur la machine de démo (RTX 5090), pas sur un portable.
- Les colonnes `reply` sont à faire relire par un locuteur natif : le script mesure, il ne juge pas la qualité du dioula.

| Route | Rôle |
|---|---|
| `GET /health` | État, modèle de traduction (mode, révision, réglages de génération), LLM et son modèle (public) |
| `GET /api/v1/languages` | Langues connues et activées |
| `POST /api/v1/translate` | Traduction seule, fr ↔ langue locale |
| `POST /api/v1/chat` | Tour de conversation (`?debug=true` si autorisé) |

Erreurs, toujours au même format : `{"error": {"code": "...", "message": "..."}, "request_id": "..."}` — 401 clé invalide, 422 requête ou langue invalide, 429 trop de requêtes, 503 modèle en chargement (`modele_indisponible`) ou LLM en panne (`llm_indisponible`, l'échange n'est alors pas mémorisé).

## 4. Organisation du code

```
app/
  main.py                 création de l'app, chargement unique des modèles (lifespan)
  api/routes.py           routes, authentification, contrôles d'entrée
  core/config.py          TOUTE la configuration (variables d'environnement)
  core/languages.py       seul endroit qui connaît les codes NLLB
  core/security.py        clés d'API hachées (SQLite), limitation de débit
  core/errors.py          format d'erreur uniforme
  services/translator.py  Translator : StubTranslator, NllbLoraTranslator (modèle fusionné
                          ou base + LoRA), post-traitement
  services/llm.py         LLMClient : StubLLM, GeminiLLM, OpenRouterLLM
  services/orchestrator.py pipeline MT → LLM → MT, chronométrage, replis
  services/safety.py      sorties vides / identiques / trop longues / en boucle
  services/sessions.py    sessions en mémoire avec durée de vie
config/
  system_prompt_fr.txt    consigne du LLM (phrases courtes = meilleure traduction)
  fallbacks.json          messages de repli — PLACEHOLDERS à faire traduire par un locuteur
  postprocess_rules.json  corrections de sortie, versionnées et désactivables
scripts/
  manage_keys.py          créer / lister / révoquer les clés d'API
  smoke_api.py            test rapide d'un serveur lancé
  run_scenarios.py        rejoue des messages et mesure textes + latences (CSV)
  benchmark_llm.py        comparaison des LLM (pôle LLM, campagne du 08/10)
docs/
  scenarios_dyu.csv       messages de test (à remplir avec des phrases validées)
  scenarios_results/      CSV produits par run_scenarios.py
```

## 5. Limites connues (v0.3.1)

- Sessions et limitation de débit **en mémoire** : perdues au redémarrage, un seul processus (`--workers 1`).
- Les messages de repli dioula sont des **placeholders** : à faire traduire avant toute démo.
- `normalize_input` ne fait rien encore : il attend la convention d'écriture de l'équipe.
- La réponse du LLM est nettoyée avant traduction (une seule ligne, sans puces ni markdown) : voir `clean_llm_reply` dans `services/orchestrator.py`.
- Gemini n'est plus que le LLM de secours (OpenRouter est le principal). Son modèle (`KOUMA_GEMINI_MODEL`) reste à confirmer dans AI Studio : `gemini-2.5-flash` n'est plus ouvert aux nouveaux projets. `max_output_tokens=200` peut couper une réponse si le modèle « réfléchit ».
- Scores du modèle fusionné annoncés par la carte Hugging Face (2 447 phrases) : fr→dyu BLEU 42,45 / chrF 60,24 ; dyu→fr BLEU 28,53 / chrF 51,51. Ils sont calculés sur un découpage du corpus fusionné, pas sur le jeu de test gelé : absence de fuite entraînement/test à vérifier avant de les présenter. Les traductions doivent être validées par un locuteur natif.
- Latence mesurée le 12/10 sur GTX 1650 Ti (4 Go), `num_beams=4` : `/translate` ≈ 2,2 s (médiane), `/chat` 10 à 14 s, dont ≈ 70 % de traduction. À remesurer sur la RTX 5090 avec `run_scenarios.py`.
- La réponse du LLM est traduite **phrase par phrase, en un seul lot** (`KOUMA_SPLIT_REPLY_SENTENCES=true`). Mettre `false` pour comparer avec la traduction d'un seul bloc.
- Les scores du modèle officiel sur le test sacré (144 phrases) ne sont pas encore publiés, et le test sacré attend la validation de deux locuteurs natifs.
- Pas d'audio (V2). Pas de bambara activé tant qu'il n'est pas évalué (`KOUMA_ENABLED_LANGUAGES=dyu,bam` pour l'activer).
- Licence : les poids NLLB-200 sont sous CC-BY-NC 4.0 (usage non commercial).

## 6. Historique des versions

| Version | Date | Changements |
|---|---|---|
| 0.3.1 | 13/10/2026 | Modèle officiel en révision `5c36e48`. Réponse du LLM traduite phrase par phrase en un seul lot. Plus d'avertissement `max_length` de transformers à chaque traduction. `KOUMA_MAX_NEW_TOKENS` par défaut à 64 (valeur recommandée pour le modèle). |
| 0.3.0 | 12/10/2026 | Modèle fusionné `syndou/nllb-200-dioula` (révision 6763611f) chargé sans adaptateur ; `KOUMA_NLLB_REVISION` fige la version. LLM via OpenRouter (`anthropic/claude-sonnet-5`, PR #3). `/health` expose le mode du traducteur, les réglages de génération et le modèle du LLM. Script `run_scenarios.py` pour mesurer textes et latences. |
| 0.2.0 | 05/10/2026 | Adaptateur NLLB v2 (`syndou/nllb-lora-dioula`, révision 160d1a9) testé sur GPU. Réponse du LLM nettoyée avant traduction. Panne du LLM : erreur 503 `llm_indisponible` au lieu de 500. |
| 0.1.0 | 01/10/2026 | Première API : `/health`, `/languages`, `/translate`, `/chat`, clés d'API, limitation de débit, stubs, Gemini. |
