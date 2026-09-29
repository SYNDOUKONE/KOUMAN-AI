from .translator import translate
from .llm import generate_response


def process_message(message: str) -> str:

    # 1. Dioula → Français
    text_fr = translate(
        text=message,
        source="dyu",
        target="fra"
    )

    # 2. Français → LLM
    response_fr = generate_response(text_fr)

    # 3. Français → Dioula
    response_dyu = translate(
        text=response_fr,
        source="fra",
        target="dyu"
    )

    return response_dyu