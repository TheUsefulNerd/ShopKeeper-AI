from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    LANGSMITH_API_KEY: str
    JWT_SECRET: str
    SUPABASE_DB_URL: str
    UPSTASH_REDIS_URL: str
    CORS_ORIGINS: str
    ENVIRONMENT: str = "dev"
    SUPABASE_TEST_DB_URL: str

    model_config = ConfigDict(env_file=".env")


settings = Settings()
