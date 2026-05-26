from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str

    BAILEYS_SERVICE_URL: str = ""

    WHATSAPP_GROUP_ID: str = ""
    BOT_PHONE_NUMBER: str = ""


settings = Settings()
