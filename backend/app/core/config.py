from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Haramaya University Laboratory Asset Management API"
    app_environment: str = "development"
    secret_key: SecretStr
    access_token_expire_seconds: int = 1800
    refresh_token_expire_seconds: int = 604800
    database_url: str = (
        "postgresql+asyncpg://hu_lab_app:local-dev-only@127.0.0.1:5432/"
        "hu_lab_management"
    )
    maintenance_approver_roles: str = ""
    asset_public_base_url: AnyHttpUrl | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    sql_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if len(secret.encode("utf-8")) < 32 or secret.startswith("replace-with-"):
            raise ValueError("SECRET_KEY must be a non-placeholder value of at least 32 bytes")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if "*" in origins:
            raise ValueError("Wildcard CORS origins are not allowed with credentialed requests")
        return value

    @field_validator("maintenance_approver_roles")
    @classmethod
    def validate_maintenance_approver_roles(cls, value: str) -> str:
        allowed_roles = {
            "ULMD_ADMIN",
            "MAINTENANCE_TECH",
            "LAB_MANAGER",
            "LAB_TECH",
            "AUDITOR",
        }
        roles = {role.strip().upper() for role in value.split(",") if role.strip()}
        invalid_roles = roles - allowed_roles
        if invalid_roles:
            raise ValueError(
                "MAINTENANCE_APPROVER_ROLES may contain only existing application roles"
            )
        return ",".join(sorted(roles))

    @field_validator("asset_public_base_url")
    @classmethod
    def validate_asset_public_base_url(
        cls, value: AnyHttpUrl | None
    ) -> AnyHttpUrl | None:
        if value is not None and (
            value.path not in ("", "/")
            or value.query
            or value.fragment
            or value.username
            or value.password
        ):
            raise ValueError(
                "ASSET_PUBLIC_BASE_URL must be an origin without path, query, or credentials"
            )
        return value

    @model_validator(mode="after")
    def require_https_asset_url_in_production(self) -> "Settings":
        if (
            self.app_environment.lower() == "production"
            and self.asset_public_base_url is not None
            and self.asset_public_base_url.scheme != "https"
        ):
            raise ValueError("ASSET_PUBLIC_BASE_URL must use HTTPS in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def maintenance_approval_role_names(self) -> set[str]:
        return (
            set(self.maintenance_approver_roles.split(","))
            if self.maintenance_approver_roles
            else set()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
