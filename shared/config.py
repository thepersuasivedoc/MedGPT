# shared/config.py — hard limits to avoid surprise bills

MAX_TOKENS_PER_RESPONSE = 1000     # Don't let LLM go on forever
MAX_CHUNKS_PER_QUERY = 6           # Fewer chunks = cheaper
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local HuggingFace model
LLM_MODEL = "llama3"               # Local Ollama model
CLAUDE_MODEL = "claude-haiku-4-5"  # Fastest/cheapest Claude for V2/V3
