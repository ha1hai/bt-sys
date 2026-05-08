from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    encryption_key: str

    dev_mode: bool = False
    dev_user_email: str = "dev@example.com"

    discord_webhook_url: str = ""
    line_channel_access_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
