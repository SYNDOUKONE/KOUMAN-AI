# KOUMA AI — API (v0.1)

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
pytest -q                                          # 30 tests, sans GPU ni réseau
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

# Adaptateur v2 (02/10/2026), publié sur Hugging Face, bidirectionnel
python -c "from huggingface_hub import snapshot_download as d; d('syndou/nllb-lora-dioula', revision='160d1a916d77677c9957d51a91ee120c450a9468', local_dir='models/nllb_lora_dioula_v2')"

export KOUMA_TRANSLATOR=nllb
export KOUMA_ADAPTER_FRA_DYU=models/nllb_lora_dioula_v2
export KOUMA_ADAPTER_DYU_FRA=models/nllb_lora_dioula_v2   # même dossier : adaptateur bidirectionnel
uvicorn app.main:app --env-file .env
```

L'adaptateur v2 doit afficher l'empreinte `5c3e584130c8` dans `/health`, pour les deux sens. Le dossier `final/` de la branche `dev` est l'ancienne version (29/09, 19 Mo) : ne pas l'utiliser. Le dossier `models/` est ignoré par git.

Configuration testée : GTX 1650 Ti (4 Go), fp16, `KOUMA_MAX_CONCURRENT_TRANSLATIONS=1`, environ 2 s par traduction courte. Si la mémoire GPU manque : `KOUMA_NUM_BEAMS=2`, puis `KOUMA_DEVICE=cpu`.

- Un adaptateur **par sens**. Un sens sans adaptateur utilise le modèle de base NLLB pur.
- `GET /health` affiche, pour chaque sens, l'adaptateur et l'**empreinte** de ses poids : on sait toujours quelle version tourne.
- Le premier démarrage télécharge `facebook/nllb-200-1.3B` (~5 Go). Pendant le chargement, `/health` répond `"status": "chargement"` et les autres routes 503.
- Test avec le vrai modèle : `pytest -m model` (voir `tests/test_model_integration.py`).

Pour le LLM : `export KOUMA_LLM=gemini GEMINI_API_KEY=...`. La clé ne vient **que** de l'environnement, jamais d'une requête.

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

| Route | Rôle |
|---|---|
| `GET /health` | État, implémentations, empreintes des adaptateurs (public) |
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
  services/translator.py  Translator : StubTranslator, NllbLoraTranslator, post-traitement
  services/llm.py         LLMClient : StubLLM, GeminiLLM
  services/orchestrator.py pipeline MT → LLM → MT, chronométrage, replis
  services/safety.py      sorties vides / identiques / trop longues / en boucle
  services/sessions.py    sessions en mémoire avec durée de vie
config/
  system_prompt_fr.txt    consigne du LLM (phrases courtes = meilleure traduction)
  fallbacks.json          messages de repli — PLACEHOLDERS à faire traduire par un locuteur
  postprocess_rules.json  corrections de sortie, versionnées et désactivables
```

## 5. Limites connues (v0.1)

- Sessions et limitation de débit **en mémoire** : perdues au redémarrage, un seul processus (`--workers 1`).
- Les messages de repli dioula sont des **placeholders** : à faire traduire avant toute démo.
- `normalize_input` ne fait rien encore : il attend la convention d'écriture de l'équipe.
- La réponse du LLM est nettoyée avant traduction (une seule ligne, sans puces ni markdown) : voir `clean_llm_reply` dans `services/orchestrator.py`.
- Le modèle Gemini (`KOUMA_GEMINI_MODEL`) reste à confirmer dans AI Studio : `gemini-2.5-flash` n'est plus ouvert aux nouveaux projets. `max_output_tokens=200` peut couper une réponse si le modèle « réfléchit ».
- Aucun score de qualité (BLEU/chrF par sens) n'est publié pour l'adaptateur v2 ; les traductions doivent être validées par un locuteur natif.
- Pas d'audio (V2). Pas de bambara activé tant qu'il n'est pas évalué (`KOUMA_ENABLED_LANGUAGES=dyu,bam` pour l'activer).
- Licence : les poids NLLB-200 sont sous CC-BY-NC 4.0 (usage non commercial).
