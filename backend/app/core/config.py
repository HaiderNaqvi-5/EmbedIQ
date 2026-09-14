from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = "development"
    APP_NAME: str = "EmbedIQ"
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/embediq_db"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/embediq_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Auth
    JWT_SECRET: str = "embediq_development_secret_key_change_in_production_32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 1440

    # AI & Embeddings
# AI & Embeddings
# Supported embedding providers: openai, gemini
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_API_KEY: str = "mock-key"
    EMBEDDING_DIMENSION: int = 1536

# Supported LLM providers: openai, groq
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "openai/gpt-oss-20b"

# Kept for OpenAI/backward compatibility
    LLM_API_KEY: str = "mock-key"

# Groq failover key pool
    GROQ_API_KEY_1: str = ""
    GROQ_API_KEY_2: str = ""
    GROQ_API_KEY_3: str = ""

# Number of attempts allowed per Groq key
    LLM_RETRIES_PER_KEY: int = 2
    # Crawler Operational Limits (PRD Section 11)
    MAX_PAGES_PER_BOT: int = 50
    MAX_CRAWL_DEPTH: int = 4
    HTTP_TIMEOUT_SECONDS: int = 15
    BROWSER_NAV_TIMEOUT_SECONDS: int = 30
    MAX_RESPONSE_BYTES: int = 5_000_000
    MAX_REDIRECTS: int = 5
    CRAWL_CONCURRENCY_PER_BOT: int = 5
    HTTP_RETRIES: int = 2
    PLAYWRIGHT_RETRIES: int = 1
    EMBEDDING_RETRIES: int = 3

    # RAG Retrieval Limits
    DEFAULT_TOP_K: int = 8
    MAX_TOP_K: int = 10
    MIN_SIMILARITY_THRESHOLD: float = 0.50
    TARGET_CHUNK_TOKENS: int = 600
    MAX_CHUNK_TOKENS: int = 1000
    CHUNK_OVERLAP_TOKENS: int = 100
    MAX_USER_MESSAGE_CHARS: int = 4000

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
