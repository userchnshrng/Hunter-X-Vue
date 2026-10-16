import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", f"sqlite:///{(PROJECT_ROOT / 'var' / 'hunter.db').as_posix()}"
        )
    )
    upload_root: Path = field(
        default_factory=lambda: Path(os.getenv("UPLOAD_ROOT", str(PROJECT_ROOT / "var" / "uploads")))
    )
    secure_cookies: bool = field(default_factory=lambda: os.getenv("HUNTER_ENV") == "production")
    access_minutes: int = 15
    refresh_days: int = 7


settings = Settings()
