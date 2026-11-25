"""Central configuration for IntelliForm.

Every setting has a safe default and can be overridden with an environment
variable (or a line in a local ``.env`` file). IntelliForm needs no API keys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_dotenv(path: Path | None = None) -> None:
    """Tiny .env reader (KEY=VALUE lines). Existing environment variables win."""
    path = path or BASE_DIR / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


def _num(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


@dataclass
class Settings:
    host: str = "127.0.0.1"          # localhost only: the dashboard has no login
    port: int = 5000
    headless: bool = False            # headed by default so you can review the form
    data_dir: Path = BASE_DIR / "data"
    log_dir: Path = BASE_DIR / "logs"
    dashboard_dir: Path = BASE_DIR / "dashboard"
    test_forms_dir: Path = BASE_DIR / "test_forms"
    navigation_timeout_s: float = 25.0
    action_timeout_s: float = 8.0
    form_wait_timeout_s: float = 10.0
    input_timeout_s: float = 600.0    # how long the agent waits for you
    review_timeout_s: float = 1800.0  # how long the browser stays open for review
    max_input_rounds: int = 5
    max_custom_options: int = 500
    # Origins (scheme://host:port) allowed to serve the built-in practice forms.
    # Only paths under /test_forms/ are reachable on them.
    allowed_local_origins: tuple = field(default=())

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.log_dir = Path(self.log_dir)
        if not self.allowed_local_origins:
            self.allowed_local_origins = (
                f"http://127.0.0.1:{self.port}",
                f"http://localhost:{self.port}",
            )

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        s = cls(
            host=os.environ.get("INTELLIFORM_HOST", "127.0.0.1"),
            port=int(_num("INTELLIFORM_PORT", 5000)),
            headless=_bool("INTELLIFORM_HEADLESS", False),
            navigation_timeout_s=_num("INTELLIFORM_NAV_TIMEOUT", 25),
            input_timeout_s=_num("INTELLIFORM_INPUT_TIMEOUT", 600),
            review_timeout_s=_num("INTELLIFORM_REVIEW_TIMEOUT", 1800),
        )
        if os.environ.get("INTELLIFORM_DATA_DIR"):
            s.data_dir = Path(os.environ["INTELLIFORM_DATA_DIR"])
        return s
