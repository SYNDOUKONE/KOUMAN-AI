#!/usr/bin/env python3
"""
KOUMAN AI - Benchmark LLM v2

Méthodologie :
- même prompt système pour tous les modèles ;
- même jeu de 10 messages indépendants ;
- 5 appels supplémentaires sur M01 pour la médiane de latence ;
- pas de retry automatique du benchmark ;
- les erreurs fournisseur/quota sont enregistrées et n'arrêtent pas la série ;
- la qualité sémantique reste à noter manuellement.

Usage :
    python scripts/benchmark_llm.py --models gemini:gemini-3.8-flash
    python scripts/benchmark_llm.py --models openai:gpt-6-luna
    python scripts/benchmark_llm.py --models hf:Qwen/Qwen3-4B-Instruct-2507
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import statistics
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv()

PROMPT_PATH = ROOT / "config" / "system_prompt_fr.txt"
MESSAGES_PATH = ROOT / "docs" / "messages_test_fr.txt"
RESULTS_DIR = ROOT / "docs" / "benchmark_results"

DEFAULT_MODELS = [
    "gemini:gemini-3.8-flash",
    "gemini:gemini-3.5-flash-lite",
    "openai:gpt-6-luna",
    "openai:gpt-6-sol",
]

EMOJI_RE = re.compile("[\U0001f300-\U0001faff\U00002700-\U000027bf\U0001f1e6-\U0001f1ff]")

SENTENCE_RE = re.compile(r"[.!?](?=\s|$)")
MARKDOWN_RE = re.compile(
    r"(^\s*[-*+]\s+)|(^\s*\d+[.)]\s+)|(```?|[*_#>])",
    re.MULTILINE,
)


def load_messages() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in MESSAGES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise ValueError(f"Ligne invalide dans {MESSAGES_PATH}: {line!r}")
        rows.append({"id": parts[0], "category": parts[1], "message": parts[2]})

    if len(rows) != 10:
        raise ValueError(f"Le fichier doit contenir exactement 10 messages, trouvé: {len(rows)}")
    return rows


def count_sentences(text: str) -> int:
    return len(SENTENCE_RE.findall(text))


def is_truncated(text: str, finish_reason: Any) -> bool:
    reason = str(finish_reason or "").upper()
    if any(token in reason for token in ("MAX_TOKENS", "LENGTH", "TOKEN_LIMIT")):
        return True

    stripped = text.rstrip()
    if not stripped:
        return False
    return not bool(re.search(r'[.!?…]["»”\']*$', stripped))


def evaluate_form(text: str, finish_reason: Any) -> dict[str, Any]:
    sentence_count = count_sentences(text)
    markdown = bool(MARKDOWN_RE.search(text))
    emoji = bool(EMOJI_RE.search(text))
    parentheses = "(" in text or ")" in text
    truncated = is_truncated(text, finish_reason)

    compliant = (
        1 <= sentence_count <= 3
        and not markdown
        and not emoji
        and not parentheses
        and not truncated
    )

    return {
        "sentence_count": sentence_count,
        "markdown": markdown,
        "emoji": emoji,
        "parentheses": parentheses,
        "truncated": truncated,
        "compliant": compliant,
    }


def call_gemini(model: str, messages: list[dict[str, str]], system_prompt: str) -> tuple[str, str]:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY absent")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=20_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    # Conversion explicite vers les objets Content/Part du SDK Google.
    contents = [
        types.Content(
            role=item["role"],
            parts=[types.Part.from_text(text=item["content"])],
        )
        for item in messages
    ]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=200,
        ),
    )

    finish_reason = ""
    if getattr(response, "candidates", None):
        finish_reason = getattr(response.candidates[0], "finish_reason", "")

    return (response.text or "").strip(), str(finish_reason)


def call_openai(model: str, messages: list[dict[str, str]], system_prompt: str) -> tuple[str, str]:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY absent")

    client = OpenAI(
        api_key=api_key,
        timeout=20.0,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model=model,
        max_completion_tokens=200,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
    )

    choice = response.choices[0]
    return (
        (choice.message.content or "").strip(),
        str(choice.finish_reason or ""),
    )


def call_hf(model: str, messages: list[dict[str, str]], system_prompt: str) -> tuple[str, str]:
    from huggingface_hub import InferenceClient

    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN absent")

    client = InferenceClient(
        token=token,
        timeout=20,
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        max_tokens=200,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
    )

    choice = response.choices[0]
    return (
        (choice.message.content or "").strip(),
        str(choice.finish_reason or ""),
    )


def call_openrouter(
    model: str,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> tuple[str, str]:
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY absent")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=60.0,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
    )

    choice = response.choices[0]

    return (
        (choice.message.content or "").strip(),
        str(choice.finish_reason or ""),
    )


def call_model(
    spec: str,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> tuple[str, str]:
    provider, model = spec.split(":", 1)
    if provider == "gemini":
        return call_gemini(model, messages, system_prompt)
    if provider == "openai":
        return call_openai(model, messages, system_prompt)
    if provider == "hf":
        return call_hf(model, messages, system_prompt)
    if provider == "openrouter":
        return call_openrouter(model, messages, system_prompt)
    raise ValueError(f"Provider inconnu: {provider!r}")


def run_benchmark_for_model(
    spec: str,
    messages: list[dict[str, str]],
    system_prompt: str,
    raw_writer: csv.DictWriter,
    latency_runs: int,
) -> dict[str, Any]:
    eval_ok = 0
    eval_errors = 0
    truncated_count = 0
    compliant_count = 0

    for item in messages:
        started = time.perf_counter()
        response = ""
        finish_reason = ""
        error = ""

        try:
            response, finish_reason = call_model(
                spec,
                [{"role": "user", "content": item["message"]}],
                system_prompt,
            )
            eval_ok += 1
            metrics = evaluate_form(response, finish_reason)
            truncated_count += int(metrics["truncated"])
            compliant_count += int(metrics["compliant"])
        except Exception as exc:
            eval_errors += 1
            error = f"{type(exc).__name__}: {exc}"
            metrics = {
                "sentence_count": "",
                "markdown": "",
                "emoji": "",
                "parentheses": "",
                "truncated": "",
                "compliant": "",
            }

        latency = time.perf_counter() - started

        raw_writer.writerow(
            {
                "model": spec,
                "message_id": item["id"],
                "category": item["category"],
                "message": item["message"],
                "response": response,
                "latency_s": round(latency, 3),
                "finish_reason": finish_reason,
                **metrics,
                "quality_1_5": "",
                "quality_comment": "",
                "error": error,
            }
        )

        if error:
            print(f"{item['id']} ERROR | {latency:.2f}s | {error}")
        else:
            print(f"{item['id']} OK | {latency:.2f}s")

    latency_values: list[float] = []
    latency_errors = 0

    if eval_ok > 0 and latency_runs > 0:
        print(f"-- latence: {latency_runs} appels sur M01 --")

        for run in range(1, latency_runs + 1):
            started = time.perf_counter()
            try:
                call_model(
                    spec,
                    [{"role": "user", "content": messages[0]["message"]}],
                    system_prompt,
                )
                value = time.perf_counter() - started
                latency_values.append(value)
                print(f"run {run}: {value:.2f}s")
            except Exception as exc:
                latency_errors += 1
                print(f"run {run}: ERROR | {type(exc).__name__}: {exc}")

    return {
        "model": spec,
        "eval_ok": eval_ok,
        "eval_errors": eval_errors,
        "truncated_count": truncated_count,
        "compliant_count": compliant_count,
        "compliance_rate": (round(compliant_count / eval_ok, 3) if eval_ok else ""),
        "latency_median_s": (round(statistics.median(latency_values), 3) if latency_values else ""),
        "latency_runs_ok": len(latency_values),
        "latency_errors": latency_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help=("Ex: gemini:gemini-3.8-flash openai:gpt-6-luna hf:Qwen/Qwen3-4B-Instruct-2507"),
    )
    parser.add_argument("--latency-runs", type=int, default=5)
    args = parser.parse_args()

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    messages = load_messages()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    raw_csv = RESULTS_DIR / f"benchmark_raw_{timestamp}.csv"
    summary_csv = RESULTS_DIR / f"benchmark_summary_{timestamp}.csv"

    raw_fields = [
        "model",
        "message_id",
        "category",
        "message",
        "response",
        "latency_s",
        "finish_reason",
        "truncated",
        "sentence_count",
        "markdown",
        "emoji",
        "parentheses",
        "compliant",
        "quality_1_5",
        "quality_comment",
        "error",
    ]

    summary_fields = [
        "model",
        "eval_ok",
        "eval_errors",
        "truncated_count",
        "compliant_count",
        "compliance_rate",
        "latency_median_s",
        "latency_runs_ok",
        "latency_errors",
    ]

    summary_rows: list[dict[str, Any]] = []

    with raw_csv.open("w", newline="", encoding="utf-8") as raw_file:
        raw_writer = csv.DictWriter(raw_file, fieldnames=raw_fields)
        raw_writer.writeheader()

        for spec in args.models:
            print(f"\n=== {spec} ===")
            summary_rows.append(
                run_benchmark_for_model(
                    spec,
                    messages,
                    system_prompt,
                    raw_writer,
                    args.latency_runs,
                )
            )
            raw_file.flush()

    with summary_csv.open("w", newline="", encoding="utf-8") as summary_file:
        summary_writer = csv.DictWriter(
            summary_file,
            fieldnames=summary_fields,
        )
        summary_writer.writeheader()
        summary_writer.writerows(summary_rows)

    print("\nRésultats:")
    print(raw_csv)
    print(summary_csv)


if __name__ == "__main__":
    main()
