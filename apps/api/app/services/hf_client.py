from huggingface_hub import InferenceClient

from app.core.config import get_settings


SYSTEM_PROMPT = """You answer questions using only the provided transcript context.
If the context is not enough, say that the transcript does not contain enough information.
Keep the answer clear and cite timestamps when useful."""


async def answer_with_context(question: str, context_blocks: list[str]) -> str:
    settings = get_settings()
    context = "\n\n".join(context_blocks)

    if not settings.hf_token:
        return _fallback_answer(question, context_blocks)

    try:
        client = InferenceClient(api_key=settings.hf_token)
        completion = client.chat.completions.create(
            model=settings.hf_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Transcript context:\n{context}\n\nQuestion: {question}",
                },
            ],
            max_tokens=500,
        )
        return completion.choices[0].message.content or _fallback_answer(
            question, context_blocks
        )
    except Exception as exc:
        return (
            "I found relevant transcript sections, but the Hugging Face request failed. "
            f"Local fallback:\n\n{_fallback_answer(question, context_blocks)}\n\n"
            f"HF error: {exc}"
        )


def _fallback_answer(question: str, context_blocks: list[str]) -> str:
    best_context = context_blocks[0] if context_blocks else ""
    if not best_context:
        return "I could not find enough transcript context to answer that."

    return (
        "Based on the most relevant transcript section, here is the useful context:\n\n"
        f"{best_context}\n\n"
        "Add `HF_TOKEN` in `apps/api/.env` to generate polished LLM answers."
    )

