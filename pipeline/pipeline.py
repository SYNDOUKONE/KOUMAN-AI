from .translator import translate
from .llm import generate_response


SUPPORTED_LANGUAGES = ["dyu"]


def process_message(message: str, language: str) -> str:

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Langue non supportée : {language}"
        )

    # 1. Langue utilisateur → Français
    text_fr = translate(
        text=message,
        source=language,
        target="fra"
    )

    # 2. Français → LLM
    response_fr = generate_response(text_fr)

    # 3. Français → Langue utilisateur
    response = translate(
        text=response_fr,
        source="fra",
        target=language
    )

    return response