# shared/llm.py
#
# Unified text-generation helper for the V2/V3 *generation* steps
# (visual explainer, Instagram script). NOT used by V1 — the V1 RAG
# tool-calling agent stays on Ollama via langchain.
#
# Two backends, selected by GENERATION_BACKEND in shared/config.py:
#   "claude-cli" -> shell out to the local `claude` CLI (uses your Claude Code
#                   auth, no ANTHROPIC_API_KEY needed). Higher quality, fast.
#   "ollama"     -> fully local via Ollama (VISUAL_MODEL).
#
# If "claude-cli" is selected but the `claude` binary is missing, we fall back
# to Ollama automatically so the pipeline still runs.

import shutil
import subprocess

from shared.config import (
    GENERATION_BACKEND,
    VISUAL_MODEL,
    CLAUDE_CLI_MODEL,
)


def _generate_claude_cli(prompt: str, model: str = None, timeout: int = 300) -> str:
    """Run a one-shot headless prompt through the local `claude` CLI."""
    cmd = [
        "claude",
        "-p", prompt,
        "--model", model or CLAUDE_CLI_MODEL,
        "--output-format", "text",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _generate_ollama(prompt: str, temperature: float = 0.7) -> str:
    """Run the prompt through a local Ollama model."""
    from langchain_ollama import ChatOllama  # imported lazily to keep CLI path light

    llm = ChatOllama(model=VISUAL_MODEL, temperature=temperature)
    return llm.invoke(prompt).content


def generate(prompt: str, temperature: float = 0.7, backend: str = None) -> str:
    """Generate text from `prompt` using the configured backend.

    `temperature` only applies to the Ollama backend (the `claude` CLI does
    not expose it in print mode). `backend` overrides the config default.
    """
    backend = backend or GENERATION_BACKEND

    if backend == "claude-cli":
        if shutil.which("claude"):
            try:
                return _generate_claude_cli(prompt)
            except Exception as e:
                print(f"Warning: claude CLI failed ({e}), falling back to Ollama.")
                return _generate_ollama(prompt, temperature)
        # Graceful fallback so the pipeline still runs without the CLI.
        return _generate_ollama(prompt, temperature)

    return _generate_ollama(prompt, temperature)


def active_backend() -> str:
    """Report which backend will actually be used (after availability checks)."""
    if GENERATION_BACKEND == "claude-cli" and shutil.which("claude"):
        return f"claude-cli ({CLAUDE_CLI_MODEL})"
    if GENERATION_BACKEND == "claude-cli":
        return f"ollama ({VISUAL_MODEL}) — claude CLI not found, fell back"
    return f"ollama ({VISUAL_MODEL})"
