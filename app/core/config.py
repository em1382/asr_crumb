from functools import lru_cache

from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "All-Seeding Rye"
    api_v1_str: str
    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "google_api_key"),
    )
    database_url: str = Field(
        default="postgresql+psycopg://crumb:crumb@127.0.0.1:5432/crumb",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    cors_allowed_origins: str = Field(
        validation_alias=AliasChoices(
            "CORS_ALLOWED_ORIGINS", "cors_allowed_origins"
        ),
    )
    api_key: str = Field(
        validation_alias=AliasChoices("CRUMB_API_KEY", "api_key"),
    )

    @field_validator("cors_allowed_origins", mode="after")
    @classmethod
    def cors_origins_not_empty(cls, v: str) -> str:
        if not [s.strip() for s in v.split(",") if s.strip()]:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS must list at least one origin (comma-separated)"
            )
        return v

    @computed_field
    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [
            s.strip()
            for s in self.cors_allowed_origins.split(",")
            if s.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
