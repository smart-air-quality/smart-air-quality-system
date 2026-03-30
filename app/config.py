from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    waqi_token:    str   = "demo"
    owm_api_key:   str   = "demo"
    location_city: str   = "Bangkok"
    location_lat:  float = 13.7563
    location_lon:  float = 100.5018
    host:          str   = "0.0.0.0"
    port:          int   = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
