"""Application configuration boundary."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Minimal settings object; extend from this single configuration boundary."""

    environment: str = "development"
    config_path: Path = Path("configs/default.yaml")


settings = Settings()

