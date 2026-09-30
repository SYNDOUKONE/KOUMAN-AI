import os

class ResearchService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            return
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "genai"
        except ImportError:
            try:
                import google.generativeai as ggi
                ggi.configure(api_key=self.api_key)
                self.client = ggi.GenerativeModel("gemini-2.5-flash")
                self.sdk_type = "generativeai"
            except ImportError:
                self.client = None

    def search_and_explain(self, query: str, context: str = "") -> dict:
        if not self.api_key:
            return {
                "success": False,
                "error": "Clé API Gemini non configurée. Veuillez définir GEMINI_API_KEY dans votre environnement.",
                "response": None
            }

        prompt = f"""Tu es Kouman AI, un assistant linguiste expert de la langue Dioula (et des langues Mandingues) et de la culture ouest-africaine.

Contexte de la demande (traduction ou phrase analysée) : {context}

Question/Recherche de l'utilisateur : {query}

Fournis une réponse claire, structurée et pédagogique en français, expliquant les éléments culturels, grammaticaux, ou contextuels importants.
"""

        try:
            if hasattr(self, 'sdk_type') and self.sdk_type == "genai":
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                answer = response.text
            else:
                import google.generativeai as ggi
                model = ggi.GenerativeModel("gemini-2.5-flash")
                res = model.generate_content(prompt)
                answer = res.text

            return {
                "success": True,
                "query": query,
                "response": answer
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
