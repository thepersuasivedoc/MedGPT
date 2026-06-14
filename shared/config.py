# shared/config.py — hard limits to avoid surprise bills

MAX_TOKENS_PER_RESPONSE = 1500     # Don't let LLM go on forever
MAX_CHUNKS_PER_QUERY = 20           # Fewer chunks = cheaper
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local HuggingFace model
NORMAL_MODEL = "llama3.1"            # Local Ollama model for fast V1 mode
DEEP_DIVE_MODEL = "llama3.1"         # Local Ollama model for intelligent diagram generation
VISUAL_MODEL = "llama3.1"            # Local Ollama model for V2/V3 generation (used when backend = "ollama")
CLAUDE_MODEL = "claude-haiku-4-5"  # Fastest/cheapest Claude for V2/V3

# ─── Generation backend for Visual Explainer and Video Generator (Normal Mode stays on Ollama) ───
# "claude-cli": shell out to the local `claude` CLI (uses your Claude Code auth, no API key needed)
# "ollama":     fully local via Ollama (VISUAL_MODEL above)
GENERATION_BACKEND = "ollama"
CLAUDE_CLI_MODEL = "haiku"           # alias passed to `claude --model` (haiku/sonnet/opus or full id)
