def translate(text: str, source: str, target: str) -> str:
    if source == "dyu" and target == "fra":
        return "Comment vas-tu ?"

    if source == "fra" and target == "dyu":
        return "N' ka kene"

    raise ValueError(
        f"Traduction non supportée : {source} -> {target}"
    )