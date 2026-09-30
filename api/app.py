import os
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from api.translation_service import TranslationService
from api.research_service import ResearchService

app = FastAPI(
    title="Kouman AI - API de Traduction & Recherche Dioula",
    description="API Hybride : NLLB-1.3B Fine-Tuné (Traduction NMT) + Gemini API (Recherche & Explications culturelles)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
translation_service = TranslationService()

class TranslationRequest(BaseModel):
    text: str = Field(..., example="Bonjour, comment vas-tu ?")
    src_lang: str = Field(default="fra_Latn", example="fra_Latn")
    tgt_lang: str = Field(default="dyu_Latn", example="dyu_Latn")
    num_beams: int = Field(default=4, ge=1, le=10)

class TranslationResponse(BaseModel):
    source_text: str
    translated_text: str
    src_lang: str
    tgt_lang: str

class ResearchRequest(BaseModel):
    query: str = Field(..., example="Que signifie l'expression 'barika da' en Dioula ?")
    context: Optional[str] = Field(default="", example="Contextual background or phrase")
    gemini_api_key: Optional[str] = Field(default=None, description="Clé API Gemini optionnelle si non définie côté serveur")

class SmartRequest(BaseModel):
    text: str = Field(..., example="Je vais au marché pour acheter de la nourriture.")
    ask_explanation: bool = Field(default=True, description="Si vrai, demande à Gemini des explications grammaticales/culturelles sur la traduction")
    gemini_api_key: Optional[str] = Field(default=None)

@app.on_event("startup")
def startup_event():
    print("Démarrage de l'API Kouman AI...", flush=True)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Kouman AI API",
        "model_nllb": "facebook/nllb-200-1.3B + LoRA (dioula)",
        "endpoints": {
            "/api/v1/translate": "POST - Traduction directe via NLLB LoRA",
            "/api/v1/research": "POST - Recherche culturelle et linguistique via Gemini",
            "/api/v1/smart": "POST - Pipeline combiné Traduction NLLB + Analyse Gemini"
        }
    }

@app.post("/api/v1/translate", response_model=TranslationResponse)
def translate_endpoint(req: TranslationRequest):
    try:
        translated = translation_service.translate(
            text=req.text,
            src_lang=req.src_lang,
            tgt_lang=req.tgt_lang,
            num_beams=req.num_beams
        )
        return TranslationResponse(
            source_text=req.text,
            translated_text=translated,
            src_lang=req.src_lang,
            tgt_lang=req.tgt_lang
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de traduction : {str(e)}")

@app.post("/api/v1/research")
def research_endpoint(req: ResearchRequest, x_gemini_key: Optional[str] = Header(None)):
    api_key = req.gemini_api_key or x_gemini_key or os.environ.get("GEMINI_API_KEY")
    research_svc = ResearchService(api_key=api_key)
    res = research_svc.search_and_explain(query=req.query, context=req.context)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/v1/smart")
def smart_endpoint(req: SmartRequest, x_gemini_key: Optional[str] = Header(None)):
    # Step 1: Traduction avec NLLB Fine-Tuné
    try:
        translated = translation_service.translate(
            text=req.text,
            src_lang="fra_Latn",
            tgt_lang="dyu_Latn"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de traduction NLLB: {str(e)}")

    response_data = {
        "source_text": req.text,
        "translated_text": translated,
        "explanation": None
    }

    # Step 2: Recherche / Explication avec Gemini si demandée
    if req.ask_explanation:
        api_key = req.gemini_api_key or x_gemini_key or os.environ.get("GEMINI_API_KEY")
        research_svc = ResearchService(api_key=api_key)
        
        prompt_query = f"Analyse la phrase en français '{req.text}' et sa traduction en Dioula '{translated}'. Décompose les mots clés, la grammaire et apporte des précisions culturelles utiles."
        res = research_svc.search_and_explain(query=prompt_query, context=f"Source: {req.text} | Traduction: {translated}")
        
        if res["success"]:
            response_data["explanation"] = res["response"]
        else:
            response_data["explanation_note"] = res["error"]

    return response_data
