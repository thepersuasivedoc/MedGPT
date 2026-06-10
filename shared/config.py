# shared/config.py — hard limits to avoid surprise bills

MAX_TOKENS_PER_RESPONSE = 1000     # Don't let LLM go on forever
MAX_CHUNKS_PER_QUERY = 6           # Fewer chunks = cheaper
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Local HuggingFace model
NORMAL_MODEL = "llama3.1"            # Local Ollama model for fast V1 mode
DEEP_DIVE_MODEL = "qwen2.5"          # Local Ollama model for intelligent diagram generation
CLAUDE_MODEL = "claude-haiku-4-5"  # Fastest/cheapest Claude for V2/V3
