import asyncio

from huggingface_hub import InferenceClient

from app.core.config import get_settings


SYSTEM_PROMPT = """You answer questions using only the provided transcript context.
If the context is not enough, say that the transcript does not contain enough information.
Keep the answer clear and cite timestamps when useful."""


async def answer_with_context(question: str, context_blocks: list[str]) -> str:
    settings = get_settings()
    context = "\n\n".join(context_blocks)

    if not settings.hf_token:
        print("[hf] HF_TOKEN is empty. Using local fallback answer.", flush=True)
        return _fallback_answer(question, context_blocks)

    try:
        print(
            f"[hf] Requesting answer from model={settings.hf_model} "
            f"timeout={settings.hf_timeout_seconds}s.",
            flush=True,
        )
        answer = await asyncio.wait_for(
            asyncio.to_thread(
                _request_hf_answer,
                settings.hf_token,
                settings.hf_model,
                question,
                context,
            ),
            timeout=settings.hf_timeout_seconds,
        )
        print(f"[hf] Received answer preview: {_preview(answer)}", flush=True)
        return answer or _fallback_answer(question, context_blocks)
    except asyncio.TimeoutError:
        print("[hf] Request timed out. Using local fallback answer.", flush=True)
        return (
            "The hosted AI model took too long to respond, so I used the local transcript fallback instead.\n\n"
            f"{_fallback_answer(question, context_blocks)}"
        )
    except Exception as exc:
        print(f"[hf] Request failed: {exc}", flush=True)
        return (
            "I found relevant transcript sections, but the Hugging Face request failed. "
            f"Local fallback:\n\n{_fallback_answer(question, context_blocks)}\n\n"
            f"HF error: {exc}"
        )


def _request_hf_answer(hf_token: str, hf_model: str, question: str, context: str) -> str:
    client = InferenceClient(api_key=hf_token)
    completion = client.chat.completions.create(
        model=hf_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Transcript context:\n{context}\n\nQuestion: {question}",
            },
        ],
        max_tokens=500,
    )
    return completion.choices[0].message.content or ""


def _fallback_answer(question: str, context_blocks: list[str]) -> str:
    best_context = context_blocks[0] if context_blocks else ""
    if not best_context:
        return "I could not find enough transcript context to answer that."

    return (
        "Based on the most relevant transcript section, here is the useful context:\n\n"
        f"{best_context}\n\n"
        "Add `HF_TOKEN` in `apps/api/.env` to generate polished LLM answers."
    )


def _preview(value: str, limit: int = 180) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."
