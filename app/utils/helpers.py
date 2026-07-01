"""LLM utility — supports Ollama (local) and Groq (cloud) backends."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _is_local() -> bool:
    """Check if we should use Ollama (local) or Groq (cloud).

    Uses GROQ_API_KEY presence as the signal:
      - If GROQ_API_KEY is set → use Groq cloud
      - Otherwise → use Ollama locally
    """
    return not os.getenv("GROQ_API_KEY")


@lru_cache(maxsize=1)
def get_llm():
    """Return a configured LLM — Ollama for local dev, Groq for production."""
    if _is_local():
        # ---------- Local: Ollama ----------
        from langchain_community.llms import Ollama

        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        print(f"[LLM] Using Ollama (model={ollama_model}, base={ollama_base})")
        return Ollama(
            model=ollama_model,
            base_url=ollama_base,
            temperature=0.1,
        )
    else:
        # ---------- Cloud: Groq ----------
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        print(f"[LLM] Using Groq (model={groq_model})")
        return ChatGroq(
            model=groq_model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=2048,
        )


def llm_invoke(prompt: str) -> str:
    """Invoke the LLM with a prompt and return the text response."""
    llm = get_llm()
    response = llm.invoke(prompt)
    # Ollama returns a string, ChatGroq returns an AIMessage
    if hasattr(response, "content"):
        return response.content.strip()
    return str(response).strip()
